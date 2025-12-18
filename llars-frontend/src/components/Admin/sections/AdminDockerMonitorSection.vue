<template>
  <div class="docker-monitor">
    <!-- Header -->
    <div class="monitor-header">
      <div class="header-left">
        <v-icon size="24">mdi-docker</v-icon>
        <h2>Docker Monitor</h2>
        <LTag :variant="connectionVariant" :prepend-icon="connectionIcon" size="small">
          {{ connectionLabel }}
        </LTag>
        <div v-if="connectionState === 'connected'" class="live-pulse"></div>
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

    <!-- Main Content -->
    <div class="monitor-content">
      <!-- Left Panel: Charts & Stats -->
      <div class="charts-panel">
        <!-- Stats Summary -->
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

        <!-- Live Charts -->
        <div class="charts-grid">
          <!-- CPU Chart -->
          <div class="chart-card">
            <div class="chart-header">
              <div class="chart-title">
                <v-icon size="18" color="primary">mdi-chip</v-icon>
                <span>CPU</span>
              </div>
              <div class="chart-value chart-value--primary">
                {{ formatPercent(summary.cpu_total_percent) }}
              </div>
            </div>
            <div class="chart-container">
              <LiveChart
                :values="summaryCpuHistory"
                :max-points="MAX_POINTS"
                color="#b0ca97"
                :height="100"
                :min-value="0"
                :max-value="100"
                unit="%"
              />
            </div>
          </div>

          <!-- Memory Chart -->
          <div class="chart-card">
            <div class="chart-header">
              <div class="chart-title">
                <v-icon size="18" color="accent">mdi-memory</v-icon>
                <span>Memory</span>
              </div>
              <div class="chart-value chart-value--accent">
                {{ formatBytes(summary.mem_total_bytes) }}
              </div>
            </div>
            <div class="chart-container">
              <LiveChart
                :values="summaryMemHistoryMiB"
                :max-points="MAX_POINTS"
                color="#88c4c8"
                :height="100"
                :min-value="0"
                unit="MiB"
              />
            </div>
          </div>

          <!-- Network RX Chart -->
          <div class="chart-card">
            <div class="chart-header">
              <div class="chart-title">
                <v-icon size="18" color="info">mdi-download</v-icon>
                <span>Network RX</span>
              </div>
              <div class="chart-value chart-value--info">
                {{ formatBytesRate(netRxRate) }}/s
              </div>
            </div>
            <div class="chart-container">
              <LiveChart
                :values="netRxRateHistory"
                :max-points="MAX_POINTS"
                color="#a8c5e2"
                :height="100"
                :min-value="0"
                unit="KB/s"
              />
            </div>
          </div>

          <!-- Network TX Chart -->
          <div class="chart-card">
            <div class="chart-header">
              <div class="chart-title">
                <v-icon size="18" color="warning">mdi-upload</v-icon>
                <span>Network TX</span>
              </div>
              <div class="chart-value chart-value--warning">
                {{ formatBytesRate(netTxRate) }}/s
              </div>
            </div>
            <div class="chart-container">
              <LiveChart
                :values="netTxRateHistory"
                :max-points="MAX_POINTS"
                color="#e8c87a"
                :height="100"
                :min-value="0"
                unit="KB/s"
              />
            </div>
          </div>
        </div>

        <!-- Selected Container Charts -->
        <div v-if="selectedContainer" class="selected-charts">
          <div class="section-header">
            <v-icon size="18">mdi-chart-line</v-icon>
            <span>{{ selectedContainer.name }}</span>
            <LBtn variant="text" size="small" prepend-icon="mdi-close" @click="selectedContainerId = null">
              Schließen
            </LBtn>
          </div>
          <div class="charts-row">
            <div class="mini-chart-card">
              <div class="mini-chart-header">
                <span class="mini-chart-label">CPU</span>
                <span class="mini-chart-value">{{ formatPercent(selectedContainer.cpu_percent) }}</span>
              </div>
              <LiveChart
                :values="selectedCpuHistory"
                :max-points="MAX_POINTS"
                color="#b0ca97"
                :height="60"
                :min-value="0"
                :max-value="100"
              />
            </div>
            <div class="mini-chart-card">
              <div class="mini-chart-header">
                <span class="mini-chart-label">Memory</span>
                <span class="mini-chart-value">{{ formatBytes(selectedContainer.mem_usage) }}</span>
              </div>
              <LiveChart
                :values="selectedMemHistoryMiB"
                :max-points="MAX_POINTS"
                color="#88c4c8"
                :height="60"
                :min-value="0"
              />
            </div>
            <div class="mini-chart-card">
              <div class="mini-chart-header">
                <span class="mini-chart-label">Net RX</span>
                <span class="mini-chart-value">{{ formatBytes(selectedContainer.net_rx) }}</span>
              </div>
              <LiveChart
                :values="selectedNetRxHistory"
                :max-points="MAX_POINTS"
                color="#a8c5e2"
                :height="60"
                :min-value="0"
              />
            </div>
            <div class="mini-chart-card">
              <div class="mini-chart-header">
                <span class="mini-chart-label">Net TX</span>
                <span class="mini-chart-value">{{ formatBytes(selectedContainer.net_tx) }}</span>
              </div>
              <LiveChart
                :values="selectedNetTxHistory"
                :max-points="MAX_POINTS"
                color="#e8c87a"
                :height="60"
                :min-value="0"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Right Panel: Table & Logs -->
      <div class="data-panel">
        <!-- Container Table -->
        <div class="table-section">
          <div class="section-header">
            <v-icon size="18">mdi-view-list</v-icon>
            <span>Container</span>
            <LTag variant="gray" size="small" class="ml-auto">{{ containers.length }}</LTag>
          </div>
          <div class="table-wrapper">
            <table class="container-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>State</th>
                  <th>Health</th>
                  <th>CPU</th>
                  <th>RAM</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="container in containers"
                  :key="container.id"
                  :class="{ 'selected': container.id === selectedContainerId }"
                  @click="selectContainer(container)"
                >
                  <td class="name-cell">{{ container.name }}</td>
                  <td><LTag :variant="stateVariant(container.state)" size="small">{{ container.state }}</LTag></td>
                  <td><LTag :variant="healthVariant(container.health)" size="small">{{ container.health || '—' }}</LTag></td>
                  <td class="value-cell">{{ formatPercent(container.cpu_percent) }}</td>
                  <td class="value-cell">
                    <span>{{ formatPercent(container.mem_percent) }}</span>
                    <span class="sub-value">({{ formatBytes(container.mem_usage) }})</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Logs Panel -->
        <div class="logs-section">
          <div class="section-header">
            <v-icon size="18">mdi-text-box-outline</v-icon>
            <span>Logs</span>
            <div class="header-controls">
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
            <v-select v-model="logMode" :items="logModeOptions" variant="outlined" density="compact" hide-details class="log-field" />
            <v-select v-model="logScope" :items="scopeOptions" variant="outlined" density="compact" hide-details class="log-field" />
            <v-select v-model="logContainerId" :items="containerOptions" variant="outlined" density="compact" hide-details :disabled="logMode !== 'container'" class="log-field" />
            <v-text-field v-model.number="logTail" type="number" label="Tail" variant="outlined" density="compact" hide-details min="0" max="5000" class="log-field log-field--small" />
            <v-switch v-model="autoScroll" color="primary" hide-details density="compact" label="Scroll" class="log-switch" />
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

const MAX_POINTS = 60
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
  cpu_total_percent: 0, mem_total_bytes: 0,
  net_rx_bytes: 0, net_tx_bytes: 0
})

// History arrays for charts
const summaryCpuHistory = ref([])
const summaryMemHistory = ref([])
const summaryNetRxHistory = ref([])
const summaryNetTxHistory = ref([])

// Network rate calculation
const lastNetRx = ref(0)
const lastNetTx = ref(0)
const netRxRate = ref(0)
const netTxRate = ref(0)
const netRxRateHistory = ref([])
const netTxRateHistory = ref([])

const selectedContainerId = ref(null)
const selectedCpuHistory = ref([])
const selectedMemHistory = ref([])
const selectedNetRxHistory = ref([])
const selectedNetTxHistory = ref([])

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

const formatBytesRate = (bytesPerSec) => {
  const b = Number(bytesPerSec || 0)
  if (!Number.isFinite(b) || b <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const idx = Math.min(units.length - 1, Math.floor(Math.log(b) / Math.log(1024)))
  const n = b / Math.pow(1024, idx)
  return `${n.toFixed(n >= 10 ? 0 : 1)} ${units[idx]}`
}

const bytesToMiB = (bytes) => Number(bytes || 0) / 1024 / 1024
const bytesToKiB = (bytes) => Number(bytes || 0) / 1024
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

const pushHistoryPoint = (arrRef, value, maxPoints = MAX_POINTS) => {
  arrRef.value.push(Number(value || 0))
  if (arrRef.value.length > maxPoints) arrRef.value.splice(0, arrRef.value.length - maxPoints)
}

const selectContainer = (item) => {
  if (selectedContainerId.value === item?.id) {
    selectedContainerId.value = null
    return
  }
  selectedContainerId.value = item?.id || null
  selectedCpuHistory.value = []
  selectedMemHistory.value = []
  selectedNetRxHistory.value = []
  selectedNetTxHistory.value = []
  if (item) {
    pushHistoryPoint(selectedCpuHistory, item.cpu_percent)
    pushHistoryPoint(selectedMemHistory, item.mem_usage)
    pushHistoryPoint(selectedNetRxHistory, bytesToKiB(item.net_rx))
    pushHistoryPoint(selectedNetTxHistory, bytesToKiB(item.net_tx))
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
    const newSummary = payload.summary || summary.value
    summary.value = newSummary
    setLoading('summary', false); setLoading('table', false); setLoading('detail', false)

    // Update history
    pushHistoryPoint(summaryCpuHistory, newSummary.cpu_total_percent)
    pushHistoryPoint(summaryMemHistory, newSummary.mem_total_bytes)

    // Calculate network rate (bytes per second, assuming ~5s interval)
    const currentNetRx = newSummary.net_rx_bytes || 0
    const currentNetTx = newSummary.net_tx_bytes || 0

    if (lastNetRx.value > 0 && currentNetRx >= lastNetRx.value) {
      netRxRate.value = (currentNetRx - lastNetRx.value) / 5
    }
    if (lastNetTx.value > 0 && currentNetTx >= lastNetTx.value) {
      netTxRate.value = (currentNetTx - lastNetTx.value) / 5
    }

    lastNetRx.value = currentNetRx
    lastNetTx.value = currentNetTx

    pushHistoryPoint(netRxRateHistory, bytesToKiB(netRxRate.value))
    pushHistoryPoint(netTxRateHistory, bytesToKiB(netTxRate.value))
    pushHistoryPoint(summaryNetRxHistory, currentNetRx)
    pushHistoryPoint(summaryNetTxHistory, currentNetTx)

    // Update selected container history
    const selected = selectedContainer.value
    if (selected) {
      pushHistoryPoint(selectedCpuHistory, selected.cpu_percent)
      pushHistoryPoint(selectedMemHistory, selected.mem_usage)
      pushHistoryPoint(selectedNetRxHistory, bytesToKiB(selected.net_rx))
      pushHistoryPoint(selectedNetTxHistory, bytesToKiB(selected.net_tx))
    } else if (selectedContainerId.value) {
      selectedContainerId.value = null
      selectedCpuHistory.value = []
      selectedMemHistory.value = []
      selectedNetRxHistory.value = []
      selectedNetTxHistory.value = []
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

// LiveChart Component
const LiveChart = defineComponent({
  name: 'LiveChart',
  props: {
    values: { type: Array, default: () => [] },
    maxPoints: { type: Number, default: 60 },
    color: { type: String, default: '#b0ca97' },
    height: { type: Number, default: 100 },
    minValue: { type: Number, default: null },
    maxValue: { type: Number, default: null },
    unit: { type: String, default: '' }
  },
  setup(props) {
    const canvasRef = ref(null)
    let animationFrame = null

    const draw = () => {
      const canvas = canvasRef.value
      if (!canvas) return

      const ctx = canvas.getContext('2d')
      const dpr = window.devicePixelRatio || 1
      const rect = canvas.getBoundingClientRect()

      canvas.width = rect.width * dpr
      canvas.height = rect.height * dpr
      ctx.scale(dpr, dpr)

      const w = rect.width
      const h = rect.height
      const padding = { top: 8, right: 8, bottom: 20, left: 40 }
      const chartW = w - padding.left - padding.right
      const chartH = h - padding.top - padding.bottom

      // Clear
      ctx.clearRect(0, 0, w, h)

      const vals = props.values.slice(-props.maxPoints)
      if (vals.length < 2) {
        // Draw empty state
        ctx.strokeStyle = 'rgba(150, 150, 150, 0.2)'
        ctx.lineWidth = 1
        ctx.setLineDash([4, 4])
        ctx.beginPath()
        ctx.moveTo(padding.left, padding.top + chartH / 2)
        ctx.lineTo(w - padding.right, padding.top + chartH / 2)
        ctx.stroke()
        ctx.setLineDash([])
        return
      }

      // Calculate range
      let minVal = props.minValue !== null ? props.minValue : Math.min(...vals)
      let maxVal = props.maxValue !== null ? props.maxValue : Math.max(...vals)
      if (minVal === maxVal) {
        minVal = minVal - 1
        maxVal = maxVal + 1
      }
      const range = maxVal - minVal

      // Draw grid lines
      ctx.strokeStyle = 'rgba(150, 150, 150, 0.15)'
      ctx.lineWidth = 1
      ctx.setLineDash([2, 2])

      const gridLines = 4
      for (let i = 0; i <= gridLines; i++) {
        const y = padding.top + (chartH / gridLines) * i
        ctx.beginPath()
        ctx.moveTo(padding.left, y)
        ctx.lineTo(w - padding.right, y)
        ctx.stroke()
      }
      ctx.setLineDash([])

      // Draw Y-axis labels
      ctx.fillStyle = 'rgba(150, 150, 150, 0.7)'
      ctx.font = '10px system-ui, sans-serif'
      ctx.textAlign = 'right'
      ctx.textBaseline = 'middle'

      for (let i = 0; i <= gridLines; i++) {
        const y = padding.top + (chartH / gridLines) * i
        const value = maxVal - (range / gridLines) * i
        ctx.fillText(value.toFixed(value >= 100 ? 0 : 1), padding.left - 4, y)
      }

      // Calculate points
      const points = vals.map((v, idx) => {
        const x = padding.left + (idx / (props.maxPoints - 1)) * chartW
        const y = padding.top + chartH - ((v - minVal) / range) * chartH
        return { x, y }
      })

      // Draw gradient fill
      const gradient = ctx.createLinearGradient(0, padding.top, 0, h - padding.bottom)
      gradient.addColorStop(0, props.color + '40')
      gradient.addColorStop(1, props.color + '05')

      ctx.beginPath()
      ctx.moveTo(points[0].x, padding.top + chartH)
      points.forEach(p => ctx.lineTo(p.x, p.y))
      ctx.lineTo(points[points.length - 1].x, padding.top + chartH)
      ctx.closePath()
      ctx.fillStyle = gradient
      ctx.fill()

      // Draw line
      ctx.beginPath()
      ctx.moveTo(points[0].x, points[0].y)

      // Smooth curve using bezier
      for (let i = 1; i < points.length - 1; i++) {
        const xc = (points[i].x + points[i + 1].x) / 2
        const yc = (points[i].y + points[i + 1].y) / 2
        ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc)
      }
      if (points.length > 1) {
        ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y)
      }

      ctx.strokeStyle = props.color
      ctx.lineWidth = 2
      ctx.lineCap = 'round'
      ctx.lineJoin = 'round'
      ctx.stroke()

      // Draw current value dot
      if (points.length > 0) {
        const lastPoint = points[points.length - 1]
        ctx.beginPath()
        ctx.arc(lastPoint.x, lastPoint.y, 4, 0, Math.PI * 2)
        ctx.fillStyle = props.color
        ctx.fill()
        ctx.beginPath()
        ctx.arc(lastPoint.x, lastPoint.y, 6, 0, Math.PI * 2)
        ctx.strokeStyle = props.color + '50'
        ctx.lineWidth = 2
        ctx.stroke()
      }
    }

    watch(() => props.values, () => {
      if (animationFrame) cancelAnimationFrame(animationFrame)
      animationFrame = requestAnimationFrame(draw)
    }, { deep: true })

    onMounted(() => {
      draw()
      window.addEventListener('resize', draw)
    })

    onBeforeUnmount(() => {
      if (animationFrame) cancelAnimationFrame(animationFrame)
      window.removeEventListener('resize', draw)
    })

    return () => h('canvas', {
      ref: canvasRef,
      class: 'live-chart-canvas',
      style: { width: '100%', height: `${props.height}px` }
    })
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
  border-radius: var(--llars-radius);
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

.live-pulse {
  width: 8px;
  height: 8px;
  background: #4ade80;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7); }
  50% { box-shadow: 0 0 0 8px rgba(74, 222, 128, 0); }
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

.scope-select :deep(.v-field__outline) { border-color: rgba(255,255,255,0.3); }
.scope-select :deep(.v-field__input),
.scope-select :deep(.v-select__selection-text) { color: white; font-size: 0.85rem; }

/* Error Banner */
.error-banner {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(232, 160, 135, 0.15);
  border-left: 3px solid var(--llars-danger);
  border-radius: var(--llars-radius-xs);
  font-size: 0.85rem;
}

/* Main Content */
.monitor-content {
  flex: 1;
  display: flex;
  gap: 16px;
  min-height: 0;
  overflow: hidden;
}

/* Charts Panel */
.charts-panel {
  width: 55%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  padding-right: 4px;
}

/* Stats Row */
.stats-row {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.stat-item {
  padding: 12px 8px;
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius-sm);
  text-align: center;
  box-shadow: var(--llars-shadow-sm);
}

.stat-item--success { background: rgba(152, 212, 187, 0.2); }
.stat-item--info { background: rgba(168, 197, 226, 0.2); }
.stat-item--danger { background: rgba(232, 160, 135, 0.2); }

.stat-value {
  display: block;
  font-size: 1.25rem;
  font-weight: 700;
}

.stat-label {
  font-size: 0.65rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Charts Grid */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.chart-card {
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius-sm);
  padding: 12px;
  box-shadow: var(--llars-shadow-sm);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  font-weight: 600;
}

.chart-value {
  font-size: 1.1rem;
  font-weight: 700;
  font-family: 'SF Mono', 'Monaco', monospace;
}

.chart-value--primary { color: var(--llars-primary); }
.chart-value--accent { color: var(--llars-accent); }
.chart-value--info { color: var(--llars-info); }
.chart-value--warning { color: var(--llars-warning); }

.chart-container {
  height: 100px;
}

/* Selected Container Charts */
.selected-charts {
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius-sm);
  padding: 12px;
  box-shadow: var(--llars-shadow-sm);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  margin-bottom: 12px;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}

.charts-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.mini-chart-card {
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
  padding: 8px;
}

.mini-chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.mini-chart-label {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
}

.mini-chart-value {
  font-size: 0.8rem;
  font-weight: 600;
  font-family: 'SF Mono', monospace;
}

/* Data Panel */
.data-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
  overflow: hidden;
}

/* Table Section */
.table-section {
  flex: 1;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius-sm);
  box-shadow: var(--llars-shadow-sm);
  overflow: hidden;
}

.table-section .section-header {
  flex-shrink: 0;
  padding: 10px 14px;
  margin-bottom: 0;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.table-wrapper {
  flex: 1;
  overflow: auto;
}

.container-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.container-table th {
  position: sticky;
  top: 0;
  background: rgba(var(--v-theme-on-surface), 0.03);
  padding: 8px 12px;
  text-align: left;
  font-weight: 600;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.container-table td {
  padding: 8px 12px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.05);
}

.container-table tbody tr {
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.container-table tbody tr:hover {
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.container-table tbody tr.selected {
  background: rgba(176, 202, 151, 0.15);
}

.name-cell {
  font-weight: 500;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.value-cell {
  font-family: 'SF Mono', monospace;
  font-size: 0.8rem;
}

.sub-value {
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 0.75rem;
  margin-left: 4px;
}

/* Logs Section */
.logs-section {
  flex: 1;
  min-height: 180px;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius-sm);
  box-shadow: var(--llars-shadow-sm);
  overflow: hidden;
}

.logs-section .section-header {
  flex-shrink: 0;
  padding: 10px 14px;
  margin-bottom: 0;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.log-controls {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  flex-wrap: wrap;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.log-field { flex: 1; min-width: 90px; max-width: 130px; }
.log-field--small { max-width: 70px; min-width: 70px; }
.log-switch { flex: 0 0 auto; margin: 0; }

.logs-container {
  flex: 1;
  min-height: 0;
  overflow: auto;
  background: rgba(30, 30, 30, 0.95);
  margin: 8px;
  border-radius: var(--llars-radius-xs);
}

.logs-content {
  margin: 0;
  padding: 10px;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.75rem;
  line-height: 1.4;
  color: #e0e0e0;
  white-space: pre;
}

/* Chart Canvas */
.live-chart-canvas {
  display: block;
}

/* Scrollbars */
.charts-panel::-webkit-scrollbar,
.table-wrapper::-webkit-scrollbar,
.logs-container::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.charts-panel::-webkit-scrollbar-track,
.table-wrapper::-webkit-scrollbar-track {
  background: transparent;
}

.charts-panel::-webkit-scrollbar-thumb,
.table-wrapper::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 3px;
}

.logs-container::-webkit-scrollbar-track {
  background: rgba(255,255,255,0.05);
}

.logs-container::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.2);
  border-radius: 3px;
}

/* Responsive */
@media (max-width: 1200px) {
  .monitor-content {
    flex-direction: column;
  }

  .charts-panel {
    width: 100%;
    max-height: 400px;
  }

  .charts-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .charts-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
