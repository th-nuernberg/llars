<template>
  <div class="docker-monitor">
    <!-- Compact Header -->
    <div class="monitor-header">
      <div class="header-left">
        <v-icon size="24">mdi-docker</v-icon>
        <h2>Docker Monitor</h2>
        <LTag :variant="connectionVariant" :prepend-icon="connectionIcon" size="small">
          {{ connectionLabel }}
        </LTag>
      </div>
      <div class="header-right">
        <v-select
          v-model="scope"
          :items="scopeOptions"
          variant="outlined"
          density="compact"
          hide-details
          class="scope-select"
        />
        <LBtn prepend-icon="mdi-refresh" variant="tonal" size="small" @click="resubscribeStats">
          Refresh
        </LBtn>
      </div>
    </div>

    <!-- Error Banner -->
    <div v-if="errorMessage" class="error-banner">
      <v-icon size="18">mdi-alert-circle</v-icon>
      <span>{{ errorMessage }}</span>
    </div>

    <!-- Main Grid -->
    <div class="monitor-grid">
      <!-- Left Column -->
      <div class="left-column">
        <!-- Stats Row -->
        <div class="stats-row">
          <div class="stat-item">
            <span class="stat-value">{{ summary.total }}</span>
            <span class="stat-label">Total</span>
          </div>
          <div class="stat-item stat-item--success">
            <span class="stat-value">{{ summary.running }}</span>
            <span class="stat-label">Running</span>
          </div>
          <div class="stat-item stat-item--info">
            <span class="stat-value">{{ summary.exited }}</span>
            <span class="stat-label">Exited</span>
          </div>
          <div class="stat-item" :class="summary.unhealthy > 0 ? 'stat-item--danger' : 'stat-item--success'">
            <span class="stat-value">{{ summary.healthy }}/{{ summary.total }}</span>
            <span class="stat-label">Healthy</span>
          </div>
        </div>

        <!-- Resource Charts -->
        <div class="resource-panel">
          <div class="resource-item">
            <div class="resource-header">
              <span class="resource-label">CPU Gesamt</span>
              <span class="resource-value">{{ formatPercent(summary.cpu_total_percent) }}</span>
            </div>
            <MiniSparkline :values="summaryCpuHistory" color="primary" :height="32" />
          </div>
          <div class="resource-item">
            <div class="resource-header">
              <span class="resource-label">RAM Gesamt</span>
              <span class="resource-value">{{ formatBytes(summary.mem_total_bytes) }}</span>
            </div>
            <MiniSparkline :values="summaryMemHistoryMiB" color="accent" :height="32" />
          </div>
        </div>

        <!-- Selected Container Detail -->
        <div class="detail-panel">
          <div class="panel-title">
            <v-icon size="18">mdi-chart-line</v-icon>
            <span>Container Detail</span>
            <LTag v-if="selectedContainer" variant="primary" size="small" class="ml-auto">
              {{ selectedContainer.name }}
            </LTag>
          </div>
          <div v-if="!selectedContainer" class="empty-state-small">
            <v-icon size="24" class="empty-icon">mdi-cursor-default-click</v-icon>
            <span>Container auswählen</span>
          </div>
          <template v-else>
            <div class="resource-item">
              <div class="resource-header">
                <span class="resource-label">CPU</span>
                <span class="resource-value">{{ formatPercent(selectedContainer.cpu_percent) }}</span>
              </div>
              <MiniSparkline :values="selectedCpuHistory" color="primary" :height="28" />
            </div>
            <div class="resource-item">
              <div class="resource-header">
                <span class="resource-label">RAM</span>
                <span class="resource-value">
                  {{ formatBytes(selectedContainer.mem_usage) }}
                  <span v-if="selectedContainer.mem_limit" class="resource-limit">
                    / {{ formatBytes(selectedContainer.mem_limit) }}
                  </span>
                </span>
              </div>
              <MiniSparkline :values="selectedMemHistoryMiB" color="accent" :height="28" />
            </div>
          </template>
        </div>
      </div>

      <!-- Right Column -->
      <div class="right-column">
        <!-- Container Table -->
        <div class="table-panel">
          <div class="panel-title">
            <v-icon size="18">mdi-view-list</v-icon>
            <span>Container</span>
            <LTag variant="gray" size="small" class="ml-auto">{{ containers.length }}</LTag>
          </div>
          <div class="table-wrapper">
            <v-data-table
              :headers="tableHeaders"
              :items="containers"
              item-key="id"
              density="compact"
              :items-per-page="-1"
              fixed-header
              class="docker-table"
              @click:row="(event, { item }) => selectContainer(item)"
              :row-props="rowProps"
            >
              <template v-slot:item.state="{ item }">
                <LTag :variant="stateVariant(item.state)" size="small">{{ item.state }}</LTag>
              </template>
              <template v-slot:item.health="{ item }">
                <LTag :variant="healthVariant(item.health)" size="small">{{ item.health || '—' }}</LTag>
              </template>
              <template v-slot:item.cpu_percent="{ item }">
                <span class="table-value">{{ formatPercent(item.cpu_percent) }}</span>
              </template>
              <template v-slot:item.mem="{ item }">
                <span class="table-value">{{ formatPercent(item.mem_percent) }}</span>
                <span class="table-sub">({{ formatBytes(item.mem_usage) }})</span>
              </template>
              <template v-slot:bottom></template>
            </v-data-table>
          </div>
        </div>

        <!-- Logs Panel -->
        <div class="logs-panel">
          <div class="panel-title">
            <v-icon size="18">mdi-text-box-outline</v-icon>
            <span>Logs</span>
            <div class="panel-controls">
              <LTag v-if="logsPaused" variant="warning" size="small">pausiert</LTag>
              <LBtn :prepend-icon="logsPaused ? 'mdi-play' : 'mdi-pause'" variant="tonal" size="small" @click="toggleLogsPause">
                {{ logsPaused ? 'Live' : 'Pause' }}
              </LBtn>
              <LBtn prepend-icon="mdi-trash-can-outline" variant="tonal" size="small" @click="clearLogs">
                Leeren
              </LBtn>
            </div>
          </div>
          <div class="log-controls">
            <v-select v-model="logMode" :items="logModeOptions" variant="outlined" density="compact" hide-details class="control-field" />
            <v-select v-model="logScope" :items="scopeOptions" variant="outlined" density="compact" hide-details class="control-field" />
            <v-select v-model="logContainerId" :items="containerOptions" variant="outlined" density="compact" hide-details :disabled="logMode !== 'container'" class="control-field" />
            <v-text-field v-model.number="logTail" type="number" label="Tail" variant="outlined" density="compact" hide-details min="0" max="5000" class="control-field control-field--small" />
            <v-switch v-model="autoScroll" color="primary" hide-details density="compact" class="control-switch" />
            <LBtn prepend-icon="mdi-connection" variant="primary" size="small" @click="resubscribeLogs">Verbinden</LBtn>
          </div>
          <div ref="logsEl" class="logs-container">
            <pre class="logs-content">{{ logText }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { io } from 'socket.io-client'
import { useAuth } from '@/composables/useAuth'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'

const socketioEnableWebsocket = String(import.meta.env.VITE_SOCKETIO_ENABLE_WEBSOCKET || '').toLowerCase() === 'true'
const socketioTransports = socketioEnableWebsocket ? ['polling', 'websocket'] : ['polling']

const auth = useAuth()
const { setLoading } = useSkeletonLoading(['summary', 'table', 'detail'])

const MAX_POINTS = 120
const MAX_LOG_LINES = 2000

const connectionState = ref('disconnected')
const errorMessage = ref('')

const scopeOptions = [
  { title: 'LLARS', value: 'project' },
  { title: 'Alle', value: 'all' }
]

const scope = ref('project')
const containers = ref([])
const summary = ref({
  total: 0, running: 0, exited: 0, restarting: 0, paused: 0,
  healthy: 0, unhealthy: 0, starting: 0, no_healthcheck: 0,
  cpu_total_percent: 0, mem_total_bytes: 0
})

const summaryCpuHistory = ref([])
const summaryMemHistory = ref([])
const selectedContainerId = ref(null)
const selectedCpuHistory = ref([])
const selectedMemHistory = ref([])

const tableHeaders = [
  { title: 'Name', key: 'name', sortable: true },
  { title: 'State', key: 'state', sortable: true, width: 100 },
  { title: 'Health', key: 'health', sortable: true, width: 100 },
  { title: 'CPU', key: 'cpu_percent', sortable: true, width: 90 },
  { title: 'RAM', key: 'mem', sortable: false, width: 130 }
]

const socket = ref(null)

const connectionLabel = computed(() => {
  if (connectionState.value === 'connected') return 'Live'
  if (connectionState.value === 'connecting') return 'Verbinde...'
  if (connectionState.value === 'error') return 'Fehler'
  return 'Offline'
})

const connectionVariant = computed(() => {
  if (connectionState.value === 'connected') return 'success'
  if (connectionState.value === 'connecting') return 'warning'
  if (connectionState.value === 'error') return 'danger'
  return 'gray'
})

const connectionIcon = computed(() => {
  if (connectionState.value === 'connected') return 'mdi-wifi'
  if (connectionState.value === 'connecting') return 'mdi-wifi-sync'
  return 'mdi-wifi-off'
})

const formatPercent = (value) => `${Number(value || 0).toFixed(1)}%`
const formatBytes = (bytes) => {
  const b = Number(bytes || 0)
  if (!Number.isFinite(b) || b <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const idx = Math.min(units.length - 1, Math.floor(Math.log(b) / Math.log(1024)))
  const n = b / Math.pow(1024, idx)
  return `${n.toFixed(n >= 10 ? 1 : 2)} ${units[idx]}`
}

const bytesToMiB = (bytes) => Number(bytes || 0) / 1024 / 1024
const summaryMemHistoryMiB = computed(() => summaryMemHistory.value.map(bytesToMiB))
const selectedMemHistoryMiB = computed(() => selectedMemHistory.value.map(bytesToMiB))

const selectedContainer = computed(() => {
  if (!selectedContainerId.value) return null
  return containers.value.find((c) => c.id === selectedContainerId.value) || null
})

const stateVariant = (state) => {
  const s = String(state || '').toLowerCase()
  if (s === 'running') return 'success'
  if (s === 'exited') return 'info'
  if (s === 'restarting') return 'warning'
  return 'gray'
}

const healthVariant = (health) => {
  const h = String(health || '').toLowerCase()
  if (h === 'healthy') return 'success'
  if (h === 'unhealthy') return 'danger'
  if (h === 'starting') return 'warning'
  return 'gray'
}

const rowProps = ({ item }) => {
  if (!item) return {}
  return { class: item.id === selectedContainerId.value ? 'selected-row' : '' }
}

const pushHistoryPoint = (arrRef, value) => {
  arrRef.value.push(Number(value || 0))
  if (arrRef.value.length > MAX_POINTS) arrRef.value.splice(0, arrRef.value.length - MAX_POINTS)
}

const selectContainer = (item) => {
  selectedContainerId.value = item?.id || null
  selectedCpuHistory.value = []
  selectedMemHistory.value = []
  if (item) {
    pushHistoryPoint(selectedCpuHistory, item.cpu_percent)
    pushHistoryPoint(selectedMemHistory, item.mem_usage)
  }
}

const resubscribeStats = () => {
  if (!socket.value) return
  socket.value.emit('docker:unsubscribe_stats', { scope: 'project' })
  socket.value.emit('docker:unsubscribe_stats', { scope: 'all' })
  socket.value.emit('docker:subscribe_stats', { scope: scope.value })
}

const connectSocket = () => {
  const token = auth.getToken()
  if (!token) {
    connectionState.value = 'error'
    errorMessage.value = 'Kein Auth-Token gefunden.'
    setLoading('summary', false); setLoading('table', false); setLoading('detail', false)
    return
  }

  errorMessage.value = ''
  connectionState.value = 'connecting'

  const rawBaseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin
  const baseUrl = String(rawBaseUrl || '').replace(/\/+$/, '')
  const s = io(`${baseUrl}/admin`, {
    path: '/socket.io',
    transports: socketioTransports,
    upgrade: socketioEnableWebsocket,
    reconnection: true,
    reconnectionAttempts: Infinity,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 10000,
    timeout: 30000,
    pingTimeout: 120000,
    pingInterval: 30000,
    query: { token }
  })

  socket.value = s

  s.on('connect', () => { connectionState.value = 'connected'; resubscribeStats() })
  s.on('disconnect', () => { connectionState.value = 'disconnected' })
  s.on('connect_error', (err) => {
    connectionState.value = 'error'
    errorMessage.value = err?.message || 'Socket Verbindung fehlgeschlagen'
    setLoading('summary', false); setLoading('table', false); setLoading('detail', false)
  })

  s.on('docker:error', (payload) => {
    errorMessage.value = payload?.message || 'Docker Fehler'
    setLoading('summary', false); setLoading('table', false); setLoading('detail', false)
  })

  s.on('docker:stats', (payload) => {
    if (!payload?.ok) {
      errorMessage.value = payload?.error || 'Docker Snapshot fehlgeschlagen'
      setLoading('summary', false); setLoading('table', false); setLoading('detail', false)
      return
    }

    errorMessage.value = ''
    containers.value = Array.isArray(payload.containers) ? payload.containers : []
    summary.value = payload.summary || summary.value
    setLoading('summary', false); setLoading('table', false); setLoading('detail', false)

    pushHistoryPoint(summaryCpuHistory, summary.value.cpu_total_percent)
    pushHistoryPoint(summaryMemHistory, summary.value.mem_total_bytes)

    const selected = selectedContainer.value
    if (selected) {
      pushHistoryPoint(selectedCpuHistory, selected.cpu_percent)
      pushHistoryPoint(selectedMemHistory, selected.mem_usage)
    } else if (selectedContainerId.value) {
      selectedContainerId.value = null
      selectedCpuHistory.value = []
      selectedMemHistory.value = []
    }

    if (logMode.value === 'container' && logContainerId.value) {
      const exists = containers.value.some((c) => c.id === logContainerId.value)
      if (!exists) logContainerId.value = null
    }
  })
}

const disconnectSocket = () => {
  try {
    socket.value?.emit('docker:unsubscribe_stats', { scope: 'project' })
    socket.value?.emit('docker:unsubscribe_stats', { scope: 'all' })
    socket.value?.emit('docker:unsubscribe_logs')
  } catch (e) { /* ignore */ }
  socket.value?.disconnect()
  socket.value = null
}

// Logs
const logsEl = ref(null)
const logsPaused = ref(false)
const autoScroll = ref(true)
const logText = ref('')

const LOG_FLUSH_INTERVAL_MS = 150
const MAX_PENDING_LOG_LINES = 5000
const _logLines = []
const _pendingLogLines = []
let logFlushTimer = null

const logModeOptions = [{ title: 'System', value: 'system' }, { title: 'Container', value: 'container' }]
const logMode = ref('system')
const logScope = ref('project')
const logContainerId = ref(null)
const logTail = ref(200)

const containerOptions = computed(() => (containers.value || []).map((c) => ({ title: c.name, value: c.id })))

const clearLogs = () => { _logLines.length = 0; _pendingLogLines.length = 0; logText.value = '' }
const toggleLogsPause = () => { logsPaused.value = !logsPaused.value }

const scrollLogsToBottom = () => {
  if (!autoScroll.value) return
  const el = logsEl.value
  if (!el) return
  requestAnimationFrame(() => { el.scrollTop = el.scrollHeight })
}

const flushLogs = () => {
  if (_pendingLogLines.length === 0) return
  _logLines.push(..._pendingLogLines.splice(0, _pendingLogLines.length))
  if (_logLines.length > MAX_LOG_LINES) _logLines.splice(0, _logLines.length - MAX_LOG_LINES)
  logText.value = _logLines.join('\n')
  scrollLogsToBottom()
}

const scheduleFlushLogs = () => {
  if (logFlushTimer) return
  logFlushTimer = setTimeout(() => { logFlushTimer = null; flushLogs() }, LOG_FLUSH_INTERVAL_MS)
}

const resubscribeLogs = () => {
  if (!socket.value) return
  socket.value.emit('docker:unsubscribe_logs')
  const payload = { mode: logMode.value, scope: logScope.value, tail: Math.max(0, Math.min(5000, Number(logTail.value || 0))) }
  if (logMode.value === 'container') {
    if (!logContainerId.value) { errorMessage.value = 'Bitte Container auswählen'; return }
    payload.container_id = logContainerId.value
  }
  errorMessage.value = ''
  socket.value.emit('docker:subscribe_logs', payload)
}

watch(scope, (newScope) => { if (logScope.value === 'project' || logScope.value === 'all') logScope.value = newScope; resubscribeStats() })
watch(logMode, () => { if (logMode.value !== 'container') logContainerId.value = null })

onMounted(() => {
  connectSocket()
  watch(containerOptions, (opts) => { if (logMode.value === 'container' && !logContainerId.value && opts.length > 0) logContainerId.value = opts[0].value }, { immediate: true })

  const attachLogHandlers = () => {
    if (!socket.value) return
    socket.value.off('docker:log_line')
    socket.value.on('docker:log_line', (payload) => {
      if (logsPaused.value) return
      const cname = payload?.container_name ? `[${payload.container_name}] ` : ''
      const line = String(payload?.line || '')
      _pendingLogLines.push(`${cname}${line}`)
      if (_pendingLogLines.length > MAX_PENDING_LOG_LINES) _pendingLogLines.splice(0, _pendingLogLines.length - MAX_PENDING_LOG_LINES)
      scheduleFlushLogs()
    })
  }
  const stop = watch(socket, () => attachLogHandlers(), { immediate: true })
  onBeforeUnmount(() => { stop() })
})

onBeforeUnmount(() => { if (logFlushTimer) { clearTimeout(logFlushTimer); logFlushTimer = null }; disconnectSocket() })

const MiniSparkline = defineComponent({
  name: 'MiniSparkline',
  props: { values: { type: Array, default: () => [] }, color: { type: String, default: 'primary' }, height: { type: Number, default: 32 } },
  setup(props) {
    const points = computed(() => {
      const vals = (props.values || []).map((v) => Number(v || 0))
      if (vals.length < 2) return ''
      const w = 180, h = Number(props.height || 32)
      const min = Math.min(...vals), max = Math.max(...vals), span = max - min || 1
      return vals.map((v, idx) => { const x = (idx / (vals.length - 1)) * w; const y = h - ((v - min) / span) * h; return `${x.toFixed(1)},${y.toFixed(1)}` }).join(' ')
    })
    return () => {
      const w = 180, hVal = Number(props.height || 32)
      return h('svg', { height: hVal, viewBox: `0 0 ${w} ${hVal}`, class: 'sparkline', preserveAspectRatio: 'none' },
        points.value ? [h('polyline', { points: points.value, class: ['sparkline__line', `sparkline__line--${props.color}`] })]
          : [h('line', { x1: 0, y1: hVal / 2, x2: w, y2: hVal / 2, class: 'sparkline__empty' })])
    }
  }
})
</script>

<style scoped>
.docker-monitor {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px;
  gap: 12px;
}

/* Header */
.monitor-header {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--llars-gradient-primary);
  border-radius: 12px 4px 12px 4px;
  gap: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  color: white;
}

.header-left h2 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.scope-select {
  width: 100px;
  background: rgba(255,255,255,0.15);
  border-radius: 6px;
}

.scope-select :deep(.v-field__outline) {
  border-color: rgba(255,255,255,0.3);
}

.scope-select :deep(.v-field__input),
.scope-select :deep(.v-select__selection-text) {
  color: white;
  font-size: 0.85rem;
}

/* Error Banner */
.error-banner {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(232, 160, 135, 0.15);
  border-left: 3px solid var(--llars-danger);
  border-radius: 6px 2px 6px 2px;
  font-size: 0.85rem;
  color: rgb(var(--v-theme-on-surface));
}

/* Main Grid */
.monitor-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 12px;
  min-height: 0;
  overflow: hidden;
}

/* Left Column */
.left-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

/* Stats Row */
.stats-row {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.stat-item {
  padding: 10px 8px;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px 2px 8px 2px;
  text-align: center;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

.stat-item--success { background: rgba(152, 212, 187, 0.2); }
.stat-item--info { background: rgba(168, 197, 226, 0.2); }
.stat-item--danger { background: rgba(232, 160, 135, 0.2); }

.stat-value {
  display: block;
  font-size: 1.1rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
}

.stat-label {
  font-size: 0.65rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

/* Resource Panel */
.resource-panel {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: rgb(var(--v-theme-surface));
  border-radius: 10px 3px 10px 3px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

.resource-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.resource-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.resource-label {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.resource-value {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.resource-limit {
  font-weight: 400;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Detail Panel */
.detail-panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: rgb(var(--v-theme-surface));
  border-radius: 10px 3px 10px 3px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
  overflow: hidden;
}

.panel-title {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.panel-controls {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}

.empty-state-small {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 0.8rem;
}

.empty-icon { opacity: 0.4; }

/* Right Column */
.right-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

/* Table Panel */
.table-panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-radius: 10px 3px 10px 3px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
  overflow: hidden;
}

.table-panel .panel-title {
  padding: 10px 14px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.table-wrapper {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.docker-table { background: transparent; }
.docker-table :deep(thead th) {
  background: rgba(var(--v-theme-on-surface), 0.03) !important;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}
.docker-table :deep(tbody tr) { cursor: pointer; transition: background-color 0.15s ease; }
.docker-table :deep(tbody tr:hover) { background: rgba(var(--v-theme-on-surface), 0.04); }
.docker-table :deep(tbody tr.selected-row) { background: rgba(176, 202, 151, 0.15); }

.table-value { font-weight: 600; font-size: 0.85rem; }
.table-sub { font-size: 0.75rem; color: rgba(var(--v-theme-on-surface), 0.5); margin-left: 2px; }

/* Logs Panel */
.logs-panel {
  flex: 1;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-radius: 10px 3px 10px 3px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
  overflow: hidden;
}

.logs-panel .panel-title {
  flex-shrink: 0;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.log-controls {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  flex-wrap: wrap;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.control-field { flex: 1; min-width: 90px; max-width: 140px; }
.control-field--small { max-width: 70px; min-width: 70px; }
.control-switch { flex: 0 0 auto; }

.logs-container {
  flex: 1;
  min-height: 0;
  overflow: auto;
  background: rgba(30, 30, 30, 0.95);
  margin: 8px;
  border-radius: 6px 2px 6px 2px;
}

.logs-content {
  margin: 0;
  padding: 10px;
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  font-size: 0.75rem;
  line-height: 1.4;
  color: #e0e0e0;
  white-space: pre;
}

/* Sparkline */
.sparkline { width: 100%; display: block; }
.sparkline__line { fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.sparkline__line--primary { stroke: var(--llars-primary); }
.sparkline__line--accent { stroke: var(--llars-accent); }
.sparkline__empty { stroke: rgba(var(--v-theme-on-surface), 0.15); stroke-width: 1; stroke-dasharray: 4 4; }

/* Scrollbars */
.table-wrapper::-webkit-scrollbar,
.logs-container::-webkit-scrollbar { width: 6px; height: 6px; }
.table-wrapper::-webkit-scrollbar-track { background: transparent; }
.table-wrapper::-webkit-scrollbar-thumb { background: rgba(var(--v-theme-on-surface), 0.15); border-radius: 3px; }
.logs-container::-webkit-scrollbar-track { background: rgba(255,255,255,0.05); }
.logs-container::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 3px; }

/* Responsive */
@media (max-width: 900px) {
  .monitor-grid { grid-template-columns: 1fr; }
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .left-column { max-height: 300px; }
}
</style>
