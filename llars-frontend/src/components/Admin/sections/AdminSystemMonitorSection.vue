<template>
  <div class="system-monitor">
    <!-- Compact Header -->
    <div class="monitor-header">
      <div class="header-left">
        <v-icon size="24" color="white">mdi-monitor-dashboard</v-icon>
        <h2>System Monitor</h2>
        <LTag :variant="connectionVariant" :prepend-icon="connectionIcon" size="small" class="connection-tag">
          {{ connectionLabel }}
        </LTag>
        <div v-if="connectionState === 'connected' && !paused" class="live-pulse"></div>
      </div>
      <div class="header-right">
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
        <LBtn
          prepend-icon="mdi-trash-can-outline"
          variant="tonal"
          size="small"
          @click="clear"
        >
          Leeren
        </LBtn>
      </div>
    </div>

    <!-- Filters Bar -->
    <div class="filters-bar">
      <v-text-field
        v-model="search"
        placeholder="Suche (Typ, Message, User)"
        prepend-inner-icon="mdi-magnify"
        variant="outlined"
        density="compact"
        hide-details
        clearable
        class="search-field"
      />
      <v-select
        v-model="severityFilter"
        :items="severityOptions"
        placeholder="Severity"
        variant="outlined"
        density="compact"
        hide-details
        clearable
        class="severity-select"
      />
      <div class="filter-toggles">
        <v-switch
          v-model="autoScroll"
          color="primary"
          hide-details
          density="compact"
          class="auto-scroll-switch"
        >
          <template #label>
            <span class="switch-label">Auto-Scroll</span>
          </template>
        </v-switch>
      </div>
      <LTag variant="gray" size="small" prepend-icon="mdi-format-list-numbered">
        {{ filteredEvents.length }} Events
      </LTag>
    </div>

    <!-- Events Table -->
    <div class="events-container">
      <v-skeleton-loader
        v-if="isLoading('table')"
        type="table"
        class="skeleton-loader"
      />

      <div v-else class="events-table-wrapper">
        <table class="events-table">
          <thead>
            <tr>
              <th class="col-time">Zeit</th>
              <th class="col-severity">Severity</th>
              <th class="col-type">Typ</th>
              <th class="col-user">User</th>
              <th class="col-message">Message</th>
            </tr>
          </thead>
          <tbody ref="tableBody">
            <TransitionGroup name="event-row">
              <tr
                v-for="event in filteredEvents"
                :key="event.id"
                :class="['event-row', { 'event-row--new': isNewEvent(event.id) }]"
              >
                <td class="col-time">
                  <span class="time-text">{{ formatTime(event.created_at) }}</span>
                </td>
                <td class="col-severity">
                  <LTag :variant="severityVariant(event.severity)" size="small">
                    {{ event.severity }}
                  </LTag>
                </td>
                <td class="col-type">
                  <span class="type-text">{{ event.event_type }}</span>
                </td>
                <td class="col-user">
                  <span class="user-text">{{ event.username || '-' }}</span>
                </td>
                <td class="col-message">
                  <div class="message-content">
                    <span class="message-text">{{ event.message }}</span>
                    <span v-if="event.entity_type || event.entity_id" class="message-meta">
                      {{ event.entity_type || '' }}{{ event.entity_type && event.entity_id ? ':' : '' }}{{ event.entity_id || '' }}
                    </span>
                  </div>
                </td>
              </tr>
            </TransitionGroup>
          </tbody>
        </table>

        <div v-if="filteredEvents.length === 0" class="empty-state">
          <v-icon size="48" color="grey">mdi-format-list-bulleted</v-icon>
          <p>Keine Events vorhanden</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch, nextTick } from 'vue'
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'

const auth = useAuth()
const { isLoading, withLoading } = useSkeletonLoading(['table'])

const events = ref([])
const lastEventId = ref(0)
const paused = ref(false)
const autoScroll = ref(true)
const tableBody = ref(null)
const search = ref('')
const severityFilter = ref(null)
const reloading = ref(false)

// Track new events for animation
const newEventIds = ref(new Set())
const NEW_EVENT_DURATION = 2000 // ms to keep "new" state

const connectionState = ref('disconnected')
const streamAbortController = ref(null)
let reconnectTimer = null

const severityOptions = [
  { title: 'Alle', value: null },
  { title: 'success', value: 'success' },
  { title: 'info', value: 'info' },
  { title: 'warning', value: 'warning' },
  { title: 'error', value: 'error' },
  { title: 'critical', value: 'critical' }
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

const severityVariant = (severity) => {
  const s = String(severity || '').toLowerCase()
  if (s === 'success') return 'success'
  if (s === 'warning') return 'warning'
  if (s === 'error' || s === 'critical') return 'danger'
  return 'info'
}

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

const isNewEvent = (id) => newEventIds.value.has(id)

const filteredEvents = computed(() => {
  const q = String(search.value || '').trim().toLowerCase()
  const sev = severityFilter.value

  return events.value.filter((e) => {
    if (sev && String(e.severity || '').toLowerCase() !== sev) return false
    if (!q) return true

    const haystack = [
      e.event_type,
      e.message,
      e.username,
      e.entity_type,
      e.entity_id
    ].filter(Boolean).join(' ').toLowerCase()
    return haystack.includes(q)
  })
})

const markAsNew = (id) => {
  newEventIds.value.add(id)
  setTimeout(() => {
    newEventIds.value.delete(id)
  }, NEW_EVENT_DURATION)
}

const addEvent = (event) => {
  if (!event?.id) return
  if (event.id <= lastEventId.value) return
  lastEventId.value = event.id

  // Mark as new for animation
  markAsNew(event.id)

  events.value.unshift(event)
  if (events.value.length > 500) {
    events.value.length = 500
  }

  if (autoScroll.value) {
    nextTick(() => {
      const wrapper = tableBody.value?.closest('.events-table-wrapper')
      if (wrapper) wrapper.scrollTop = 0
    })
  }
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
      addEvent(parsed)
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
    const url = `/api/admin/system/events/stream?after_id=${encodeURIComponent(String(lastEventId.value || 0))}`
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
  await withLoading('table', async () => {
    const { data } = await axios.get('/api/admin/system/events', { params: { limit: 200 } })
    const list = Array.isArray(data?.events) ? data.events : []
    events.value = list.sort((a, b) => (b.id || 0) - (a.id || 0))
    lastEventId.value = events.value.length ? events.value[0].id : 0
  })
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

const clear = () => {
  events.value = []
  lastEventId.value = 0
  newEventIds.value.clear()
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

onMounted(async () => {
  await loadInitial()
  startStream()
})

onBeforeUnmount(() => {
  stopStream()
})
</script>

<style scoped>
.system-monitor {
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
  0% {
    box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(74, 222, 128, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(74, 222, 128, 0);
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
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
  max-width: 300px;
}

.severity-select {
  width: 140px;
  flex-shrink: 0;
}

.filter-toggles {
  display: flex;
  align-items: center;
}

.auto-scroll-switch {
  margin: 0;
}

.switch-label {
  font-size: 0.875rem;
  white-space: nowrap;
}

/* Events Container */
.events-container {
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

.events-table-wrapper {
  flex: 1;
  overflow: auto;
}

/* Custom Table */
.events-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.events-table thead {
  position: sticky;
  top: 0;
  z-index: 1;
  background: rgb(var(--v-theme-surface));
}

.events-table th {
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

.events-table td {
  padding: 8px 12px;
  vertical-align: top;
  border-bottom: 1px solid rgba(var(--v-border-color), calc(var(--v-border-opacity) * 0.5));
}

/* Column widths */
.col-time { width: 130px; }
.col-severity { width: 100px; }
.col-type { width: 200px; }
.col-user { width: 140px; }
.col-message { width: auto; }

.time-text {
  color: rgb(var(--v-theme-on-surface-variant));
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Mono', monospace;
  font-size: 0.8rem;
}

.type-text {
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Mono', monospace;
  font-size: 0.8rem;
  color: rgb(var(--v-theme-on-surface));
}

.user-text {
  font-weight: 500;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.message-text {
  word-break: break-word;
}

.message-meta {
  font-size: 0.75rem;
  color: rgb(var(--v-theme-on-surface-variant));
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Mono', monospace;
}

/* Event Row Animations */
.event-row {
  transition: background-color 0.3s ease, opacity 0.3s ease;
}

.event-row:hover {
  background: rgba(var(--v-theme-primary), 0.04);
}

/* New event highlight animation */
.event-row--new {
  animation: highlight-fade 2s ease-out;
}

@keyframes highlight-fade {
  0% {
    background: rgba(var(--v-theme-success), 0.25);
  }
  100% {
    background: transparent;
  }
}

/* TransitionGroup animations */
.event-row-enter-active {
  animation: slide-in 0.4s ease-out;
}

.event-row-leave-active {
  animation: fade-out 0.2s ease-out;
}

.event-row-move {
  transition: transform 0.3s ease;
}

@keyframes slide-in {
  0% {
    opacity: 0;
    transform: translateX(-20px);
  }
  100% {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes fade-out {
  0% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
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

/* Dark mode adjustments */
.v-theme--dark .monitor-header {
  background: var(--llars-gradient-hero-cool);
}

.v-theme--dark .events-table th {
  background: linear-gradient(180deg, rgb(var(--v-theme-surface)) 0%, rgba(var(--v-theme-surface), 0.98) 100%);
}

.v-theme--dark .event-row:hover {
  background: rgba(var(--v-theme-primary), 0.08);
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
}
</style>
