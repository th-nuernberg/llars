<template>
  <div class="system-monitor">
    <!-- Header -->
    <div class="monitor-header">
      <div class="header-title">
        <div class="title-icon" :class="connectionIconClass">
          <LIcon size="20" color="white">mdi-monitor-dashboard</LIcon>
        </div>
        <div>
          <h2 class="text-subtitle-1 font-weight-bold">System Events</h2>
          <div class="header-status">
            <span class="status-text" :class="statusTextClass">{{ connectionLabel }}</span>
            <span v-if="connectionState === 'connected' && !paused" class="live-dot" />
          </div>
        </div>
      </div>

      <div class="header-stats">
        <div class="stat-chip">
          <LIcon size="14">mdi-format-list-numbered</LIcon>
          <span>{{ filteredEvents.length }}</span>
        </div>
        <div class="stat-chip stat-chip--error" v-if="errorCount > 0">
          <LIcon size="14">mdi-alert-circle</LIcon>
          <span>{{ errorCount }}</span>
        </div>
        <div class="stat-chip stat-chip--warning" v-if="warningCount > 0">
          <LIcon size="14">mdi-alert</LIcon>
          <span>{{ warningCount }}</span>
        </div>
      </div>

      <div class="header-actions">
        <LBtn
          :prepend-icon="paused ? 'mdi-play' : 'mdi-pause'"
          :variant="paused ? 'primary' : 'secondary'"
          size="small"
          @click="togglePause"
        >
          {{ paused ? 'Live' : 'Pause' }}
        </LBtn>
        <LBtn prepend-icon="mdi-refresh" variant="text" size="small" :loading="reloading" @click="reload" />
        <LBtn prepend-icon="mdi-trash-can-outline" variant="text" size="small" @click="clear" />
      </div>
    </div>

    <!-- Filters Bar -->
    <div class="filters-bar">
      <div class="search-wrapper">
        <LIcon size="16" class="search-icon">mdi-magnify</LIcon>
        <input
          v-model="search"
          type="text"
          placeholder="Suche nach Typ, Message, User..."
          class="search-input"
        />
        <button v-if="search" class="search-clear" @click="search = ''">
          <LIcon size="14">mdi-close</LIcon>
        </button>
      </div>

      <div class="filter-chips">
        <button
          v-for="sev in severityChips"
          :key="sev.value"
          class="filter-chip"
          :class="{ 'filter-chip--active': severityFilter === sev.value, [`filter-chip--${sev.variant}`]: true }"
          @click="severityFilter = severityFilter === sev.value ? null : sev.value"
        >
          <LIcon size="12">{{ sev.icon }}</LIcon>
          <span>{{ sev.label }}</span>
        </button>
      </div>

      <div class="filter-toggle">
        <input type="checkbox" id="autoScroll" v-model="autoScroll" class="toggle-input" />
        <label for="autoScroll" class="toggle-label">
          <LIcon size="14">mdi-arrow-collapse-down</LIcon>
          Auto-Scroll
        </label>
      </div>
    </div>

    <!-- Events Table -->
    <div class="events-container">
      <LSkeleton v-if="isLoading('table')" type="table" :count="8" :columns="5" />

      <div v-else class="events-table-wrapper">
        <table class="events-table">
          <thead>
            <tr>
              <th class="col-time">Zeit</th>
              <th class="col-type">Typ</th>
              <th class="col-severity">Severity</th>
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
                @click="openEventDetail(event)"
              >
                <td class="col-time">
                  <span class="time-text">{{ formatTime(event.created_at) }}</span>
                </td>
                <td class="col-type">
                  <div class="type-cell">
                    <div class="type-icon" :style="{ backgroundColor: getEventStyle(event.event_type, event.severity).color }">
                      <LIcon size="12" color="white">{{ getEventStyle(event.event_type, event.severity).icon }}</LIcon>
                    </div>
                    <span class="type-text">{{ event.event_type }}</span>
                  </div>
                </td>
                <td class="col-severity">
                  <LTag :variant="severityVariant(event.severity)" size="small">
                    {{ event.severity }}
                  </LTag>
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
          <LIcon size="40" class="text-medium-emphasis">mdi-format-list-bulleted</LIcon>
          <span class="text-medium-emphasis">Keine Events vorhanden</span>
        </div>
      </div>
    </div>

    <!-- Event Detail Dialog -->
    <v-dialog v-model="eventDialog" max-width="550">
      <v-card v-if="selectedEvent" class="event-detail-card">
        <v-card-title class="d-flex align-center pa-4">
          <div class="event-detail-icon" :style="{ backgroundColor: getEventStyle(selectedEvent.event_type, selectedEvent.severity).color }">
            <LIcon size="24" color="white">{{ getEventStyle(selectedEvent.event_type, selectedEvent.severity).icon }}</LIcon>
          </div>
          <div class="ml-3 flex-grow-1">
            <div class="text-subtitle-1 font-weight-bold">{{ selectedEvent.event_type }}</div>
            <div class="text-caption text-medium-emphasis">{{ formatFullTime(selectedEvent.created_at) }}</div>
          </div>
          <LTag :variant="severityVariant(selectedEvent.severity)" size="sm">{{ selectedEvent.severity }}</LTag>
          <v-btn icon variant="text" size="small" class="ml-2" @click="eventDialog = false">
            <LIcon>mdi-close</LIcon>
          </v-btn>
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-4">
          <div class="detail-section">
            <div class="detail-label">Message</div>
            <div class="detail-value detail-value--message">{{ selectedEvent.message }}</div>
          </div>

          <div v-if="selectedEvent.username" class="detail-row">
            <span class="detail-label">Benutzer</span>
            <LTag variant="info" size="sm">{{ selectedEvent.username }}</LTag>
          </div>

          <div v-if="selectedEvent.entity_type" class="detail-row">
            <span class="detail-label">Entity Typ</span>
            <span class="detail-value">{{ selectedEvent.entity_type }}</span>
          </div>

          <div v-if="selectedEvent.entity_id" class="detail-row">
            <span class="detail-label">Entity ID</span>
            <code class="detail-code">{{ selectedEvent.entity_id }}</code>
          </div>

          <div class="detail-row">
            <span class="detail-label">Event ID</span>
            <code class="detail-code">{{ selectedEvent.id }}</code>
          </div>
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-3">
          <LBtn variant="text" size="small" prepend-icon="mdi-content-copy" @click="copyEventJson">
            JSON kopieren
          </LBtn>
          <v-spacer />
          <LBtn variant="secondary" size="small" @click="eventDialog = false">Schließen</LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
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

// Event detail dialog
const eventDialog = ref(false)
const selectedEvent = ref(null)

// Track new events for animation
const newEventIds = ref(new Set())
const NEW_EVENT_DURATION = 2000

const connectionState = ref('disconnected')
const streamAbortController = ref(null)
let reconnectTimer = null

// Severity filter chips
const severityChips = [
  { value: 'error', label: 'Error', icon: 'mdi-alert-circle', variant: 'danger' },
  { value: 'warning', label: 'Warning', icon: 'mdi-alert', variant: 'warning' },
  { value: 'info', label: 'Info', icon: 'mdi-information', variant: 'info' },
  { value: 'success', label: 'Success', icon: 'mdi-check-circle', variant: 'success' },
]

// Event style mapping
const getEventStyle = (eventType, severity) => {
  const eventStyles = {
    'auth_login': { icon: 'mdi-login', color: '#4CAF50' },
    'auth_logout': { icon: 'mdi-logout', color: '#9E9E9E' },
    'scenario_created': { icon: 'mdi-clipboard-plus', color: '#2196F3' },
    'scenario_updated': { icon: 'mdi-clipboard-edit', color: '#FF9800' },
    'scenario_deleted': { icon: 'mdi-clipboard-remove', color: '#f44336' },
    'chatbot_created': { icon: 'mdi-robot', color: '#9C27B0' },
    'chatbot_updated': { icon: 'mdi-robot-outline', color: '#9C27B0' },
    'chatbot_message': { icon: 'mdi-message-text', color: '#9C27B0' },
    'rag_upload': { icon: 'mdi-file-upload', color: '#00BCD4' },
    'rag_delete': { icon: 'mdi-file-remove', color: '#f44336' },
    'user_created': { icon: 'mdi-account-plus', color: '#4CAF50' },
    'permission_changed': { icon: 'mdi-shield-account', color: '#FF9800' },
    'system_startup': { icon: 'mdi-power', color: '#4CAF50' },
    'llm_request': { icon: 'mdi-brain', color: '#E91E63' },
  }

  if (eventStyles[eventType]) return eventStyles[eventType]
  if (severity === 'error' || severity === 'critical') return { icon: 'mdi-alert-circle', color: '#f44336' }
  if (severity === 'warning') return { icon: 'mdi-alert', color: '#FF9800' }
  if (severity === 'success') return { icon: 'mdi-check-circle', color: '#4CAF50' }
  return { icon: 'mdi-information-outline', color: '#607D8B' }
}

const connectionLabel = computed(() => {
  if (paused.value) return 'Pausiert'
  if (connectionState.value === 'connected') return 'Live'
  if (connectionState.value === 'connecting') return 'Verbinde...'
  if (connectionState.value === 'error') return 'Fehler'
  return 'Offline'
})

const connectionIconClass = computed(() => ({
  'title-icon--success': connectionState.value === 'connected' && !paused.value,
  'title-icon--warning': connectionState.value === 'connecting',
  'title-icon--danger': connectionState.value === 'error',
  'title-icon--gray': connectionState.value === 'disconnected' || paused.value,
}))

const statusTextClass = computed(() => ({
  'text-success': connectionState.value === 'connected' && !paused.value,
  'text-warning': connectionState.value === 'connecting',
  'text-error': connectionState.value === 'error',
}))

const errorCount = computed(() => events.value.filter(e => e.severity === 'error' || e.severity === 'critical').length)
const warningCount = computed(() => events.value.filter(e => e.severity === 'warning').length)

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
    return date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return iso
  }
}

const formatFullTime = (iso) => {
  try {
    return new Date(iso).toLocaleString('de-DE', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit'
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

    const haystack = [e.event_type, e.message, e.username, e.entity_type, e.entity_id]
      .filter(Boolean).join(' ').toLowerCase()
    return haystack.includes(q)
  })
})

const openEventDetail = (event) => {
  selectedEvent.value = event
  eventDialog.value = true
}

const copyEventJson = async () => {
  if (selectedEvent.value) {
    await navigator.clipboard.writeText(JSON.stringify(selectedEvent.value, null, 2))
  }
}

const markAsNew = (id) => {
  newEventIds.value.add(id)
  setTimeout(() => newEventIds.value.delete(id), NEW_EVENT_DURATION)
}

const addEvent = (event) => {
  if (!event?.id || event.id <= lastEventId.value) return
  lastEventId.value = event.id
  markAsNew(event.id)
  events.value.unshift(event)
  if (events.value.length > 500) events.value.length = 500

  if (autoScroll.value) {
    nextTick(() => {
      const wrapper = tableBody.value?.closest('.events-table-wrapper')
      if (wrapper) wrapper.scrollTop = 0
    })
  }
}

const stopStream = () => {
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
  if (streamAbortController.value) { streamAbortController.value.abort(); streamAbortController.value = null }
  if (!paused.value) connectionState.value = 'disconnected'
}

const scheduleReconnect = () => {
  if (paused.value || reconnectTimer) return
  reconnectTimer = setTimeout(() => { reconnectTimer = null; startStream() }, 2000)
}

const parseAndHandleSseChunk = (chunk, state) => {
  state.buffer += chunk
  const parts = state.buffer.split('\n\n')
  state.buffer = parts.pop() || ''

  for (const part of parts) {
    const lines = part.split('\n')
    let eventName = null, id = null
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
    } catch { /* ignore */ }
  }
}

const startStream = async () => {
  if (paused.value) return
  stopStream()

  const token = auth.getToken()
  if (!token) { connectionState.value = 'error'; return }

  connectionState.value = 'connecting'
  const controller = new AbortController()
  streamAbortController.value = controller
  const streamState = { buffer: '' }

  try {
    const url = `/api/admin/system/events/stream?after_id=${encodeURIComponent(String(lastEventId.value || 0))}`
    const response = await fetch(url, {
      method: 'GET',
      headers: { Authorization: `Bearer ${token}` },
      signal: controller.signal
    })

    if (!response.ok || !response.body) { connectionState.value = 'error'; scheduleReconnect(); return }

    connectionState.value = 'connected'
    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { value, done } = await reader.read()
      if (done || controller.signal.aborted) break
      parseAndHandleSseChunk(decoder.decode(value, { stream: true }), streamState)
    }

    if (!controller.signal.aborted) { connectionState.value = 'error'; scheduleReconnect() }
  } catch {
    if (!controller.signal.aborted) { connectionState.value = 'error'; scheduleReconnect() }
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
  try { await loadInitial(); if (!paused.value) startStream() }
  finally { reloading.value = false }
}

const clear = () => { events.value = []; lastEventId.value = 0; newEventIds.value.clear() }
const togglePause = () => { paused.value = !paused.value }

watch(paused, (val) => {
  if (val) { stopStream(); connectionState.value = 'disconnected' }
  else startStream()
})

onMounted(async () => { await loadInitial(); startStream() })
onBeforeUnmount(() => stopStream())
</script>

<style scoped>
.system-monitor {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  gap: 12px;
}

/* Header */
.monitor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.3s ease;
}

.title-icon--success { background: #4CAF50; }
.title-icon--warning { background: #FF9800; }
.title-icon--danger { background: #f44336; }
.title-icon--gray { background: #9E9E9E; }

.header-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
}

.status-text { font-weight: 600; }

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4CAF50;
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.header-stats {
  display: flex;
  gap: 8px;
}

.stat-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  background: rgba(var(--v-theme-on-surface), 0.06);
}

.stat-chip--error { background: rgba(244, 67, 54, 0.12); color: #f44336; }
.stat-chip--warning { background: rgba(255, 152, 0, 0.12); color: #FF9800; }

.header-actions {
  display: flex;
  gap: 4px;
}

/* Filters Bar */
.filters-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
}

.search-wrapper {
  position: relative;
  flex: 1;
  max-width: 280px;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.search-input {
  width: 100%;
  padding: 6px 32px 6px 32px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 6px;
  font-size: 0.8rem;
  background: transparent;
  color: rgb(var(--v-theme-on-surface));
  outline: none;
  transition: border-color 0.15s ease;
}

.search-input:focus {
  border-color: rgb(var(--v-theme-primary));
}

.search-input::placeholder {
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.search-clear {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.filter-chips {
  display: flex;
  gap: 6px;
}

.filter-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 14px;
  font-size: 0.7rem;
  font-weight: 500;
  background: transparent;
  color: rgba(var(--v-theme-on-surface), 0.6);
  cursor: pointer;
  transition: all 0.15s ease;
}

.filter-chip:hover { background: rgba(var(--v-theme-on-surface), 0.04); }

.filter-chip--active.filter-chip--danger { background: rgba(244, 67, 54, 0.12); border-color: #f44336; color: #f44336; }
.filter-chip--active.filter-chip--warning { background: rgba(255, 152, 0, 0.12); border-color: #FF9800; color: #FF9800; }
.filter-chip--active.filter-chip--info { background: rgba(33, 150, 243, 0.12); border-color: #2196F3; color: #2196F3; }
.filter-chip--active.filter-chip--success { background: rgba(76, 175, 80, 0.12); border-color: #4CAF50; color: #4CAF50; }

.filter-toggle {
  display: flex;
  align-items: center;
  margin-left: auto;
}

.toggle-input { display: none; }

.toggle-label {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  cursor: pointer;
  transition: all 0.15s ease;
}

.toggle-input:checked + .toggle-label {
  background: rgba(var(--v-theme-primary), 0.12);
  color: rgb(var(--v-theme-primary));
}

/* Events Container */
.events-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.events-table-wrapper {
  height: 100%;
  overflow: auto;
}

.events-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
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
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: rgba(var(--v-theme-on-surface), 0.5);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.events-table td {
  padding: 10px 12px;
  vertical-align: middle;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.04);
}

.col-time { width: 90px; }
.col-type { width: 180px; }
.col-severity { width: 90px; }
.col-user { width: 120px; }
.col-message { width: auto; }

.event-row {
  cursor: pointer;
  transition: background 0.15s ease;
}

.event-row:hover { background: rgba(var(--v-theme-primary), 0.04); }

.event-row--new { animation: highlight-fade 2s ease-out; }

@keyframes highlight-fade {
  0% { background: rgba(76, 175, 80, 0.2); }
  100% { background: transparent; }
}

.time-text {
  font-family: 'SF Mono', monospace;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.type-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-icon {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.type-text {
  font-family: 'SF Mono', monospace;
  font-size: 0.75rem;
}

.user-text { font-weight: 500; }

.message-content { display: flex; flex-direction: column; gap: 2px; }
.message-text { word-break: break-word; }
.message-meta {
  font-size: 0.7rem;
  font-family: 'SF Mono', monospace;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

/* TransitionGroup */
.event-row-enter-active { animation: slide-in 0.3s ease-out; }
.event-row-leave-active { animation: fade-out 0.2s ease-out; }
.event-row-move { transition: transform 0.3s ease; }

@keyframes slide-in {
  0% { opacity: 0; transform: translateX(-10px); }
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
  gap: 8px;
}

/* Event Detail Dialog */
.event-detail-card { border-radius: 12px !important; }

.event-detail-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-section { margin-bottom: 16px; }

.detail-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.detail-label {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-weight: 500;
}

.detail-value { font-size: 0.85rem; font-weight: 500; }
.detail-value--message { margin-top: 4px; line-height: 1.5; }

.detail-code {
  font-family: 'SF Mono', monospace;
  font-size: 0.8rem;
  padding: 2px 6px;
  background: rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 4px;
}

/* Responsive */
@media (max-width: 1000px) {
  .header-stats { display: none; }
  .filter-chips { display: none; }
}

@media (max-width: 700px) {
  .monitor-header { flex-wrap: wrap; gap: 8px; }
  .header-actions { width: 100%; justify-content: flex-end; }
}
</style>
