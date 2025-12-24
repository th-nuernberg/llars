<template>
  <div class="docker-monitor" :class="{ 'is-mobile': isMobile }">
    <!-- Header -->
    <div class="monitor-header">
      <div class="header-left">
        <v-icon :size="isMobile ? 20 : 24">mdi-docker</v-icon>
        <h2>{{ isMobile ? 'Docker' : 'Docker Monitor' }}</h2>
        <LTag :variant="connectionVariant" :prepend-icon="isMobile ? '' : connectionIcon" size="small">
          {{ isMobile ? '' : connectionLabel }}
        </LTag>
        <div v-if="connectionState === 'connected'" class="live-pulse"></div>
      </div>
      <div v-if="!isMobile" class="header-right">
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
      <LBtn v-else icon variant="text" size="small" @click="resubscribeStats">
        <v-icon>mdi-refresh</v-icon>
      </LBtn>
    </div>

    <!-- Error Banner -->
    <div v-if="errorMessage" class="error-banner">
      <v-icon size="18">mdi-alert-circle</v-icon>
      <span>{{ errorMessage }}</span>
    </div>

    <!-- Main Content: Vertical Layout -->
    <div class="monitor-content">
      <!-- Top Section: Stats + Charts + Container Table -->
      <div class="top-section">
        <!-- Stats Summary -->
        <div class="stats-row">
          <template v-if="isLoading('summary')">
            <div v-for="n in 4" :key="'stat-skel-' + n" class="stat-item stat-item--skeleton">
              <div class="skeleton-line skeleton-line--lg"></div>
              <div class="skeleton-line skeleton-line--sm"></div>
            </div>
          </template>
          <template v-else>
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
          </template>
        </div>

        <!-- Charts + Container Table Row -->
        <div class="charts-table-row">
          <!-- Live Charts (Desktop only) -->
          <div v-if="!isMobile" class="charts-grid">
            <div class="chart-card">
              <div class="chart-header">
                <div class="chart-title">
                  <v-icon size="16" color="primary">mdi-chip</v-icon>
                  <span>CPU</span>
                </div>
                <div class="chart-value chart-value--primary">
                  <div v-if="isLoading('charts')" class="skeleton-line skeleton-line--mono"></div>
                  <template v-else>{{ formatPercent(summary.cpu_total_percent) }}</template>
                </div>
              </div>
              <div class="chart-container">
                <div v-if="isLoading('charts')" class="chart-skeleton"></div>
                <LiveChart v-else :values="summaryCpuHistory" :max-points="MAX_POINTS" color="#b0ca97" :height="60" :min-value="0" :max-value="100" unit="%" />
              </div>
            </div>

            <div class="chart-card">
              <div class="chart-header">
                <div class="chart-title">
                  <v-icon size="16" color="accent">mdi-memory</v-icon>
                  <span>Memory</span>
                </div>
                <div class="chart-value chart-value--accent">
                  <div v-if="isLoading('charts')" class="skeleton-line skeleton-line--mono"></div>
                  <template v-else>{{ formatBytes(summary.mem_total_bytes) }}</template>
                </div>
              </div>
              <div class="chart-container">
                <div v-if="isLoading('charts')" class="chart-skeleton"></div>
                <LiveChart v-else :values="summaryMemHistoryMiB" :max-points="MAX_POINTS" color="#88c4c8" :height="60" :min-value="0" unit="MiB" />
              </div>
            </div>

            <div class="chart-card">
              <div class="chart-header">
                <div class="chart-title">
                  <v-icon size="16" color="info">mdi-download</v-icon>
                  <span>Net RX</span>
                </div>
                <div class="chart-value chart-value--info">
                  <div v-if="isLoading('charts')" class="skeleton-line skeleton-line--mono"></div>
                  <template v-else>{{ formatBytesRate(netRxRate) }}/s</template>
                </div>
              </div>
              <div class="chart-container">
                <div v-if="isLoading('charts')" class="chart-skeleton"></div>
                <LiveChart v-else :values="netRxRateHistory" :max-points="MAX_POINTS" color="#a8c5e2" :height="60" :min-value="0" unit="KB/s" />
              </div>
            </div>

            <div class="chart-card">
              <div class="chart-header">
                <div class="chart-title">
                  <v-icon size="16" color="warning">mdi-upload</v-icon>
                  <span>Net TX</span>
                </div>
                <div class="chart-value chart-value--warning">
                  <div v-if="isLoading('charts')" class="skeleton-line skeleton-line--mono"></div>
                  <template v-else>{{ formatBytesRate(netTxRate) }}/s</template>
                </div>
              </div>
              <div class="chart-container">
                <div v-if="isLoading('charts')" class="chart-skeleton"></div>
                <LiveChart v-else :values="netTxRateHistory" :max-points="MAX_POINTS" color="#e8c87a" :height="60" :min-value="0" unit="KB/s" />
              </div>
            </div>
          </div>

          <!-- Container Table -->
          <div class="table-section">
            <div class="section-header">
              <v-icon size="16">mdi-view-list</v-icon>
              <span>Container</span>
              <LTag variant="gray" size="small" class="ml-auto">{{ containers.length }}</LTag>
            </div>
            <v-skeleton-loader v-if="isLoading('table')" type="table" class="table-skeleton" />
            <div v-else class="table-wrapper">
              <table class="container-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>State</th>
                    <th v-if="!isMobile">Health</th>
                    <th v-if="!isMobile">CPU</th>
                    <th v-if="!isMobile">RAM</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="container in containers"
                    :key="container.id"
                    :class="{ 'selected': container.id === logContainerId && logMode === 'container' }"
                    @click="isMobile ? switchToContainerLogs(container) : null"
                  >
                    <td class="name-cell" @click="!isMobile && switchToContainerLogs(container)">
                      <span class="name-link">{{ container.name }}</span>
                    </td>
                    <td><LTag :variant="stateVariant(container.state)" size="small">{{ container.state }}</LTag></td>
                    <td v-if="!isMobile"><LTag :variant="healthVariant(container.health)" size="small">{{ container.health || '—' }}</LTag></td>
                    <td v-if="!isMobile" class="value-cell">{{ formatPercent(container.cpu_percent) }}</td>
                    <td v-if="!isMobile" class="value-cell">{{ formatPercent(container.mem_percent) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom Section: Logs (full width) -->
      <div class="logs-section">
        <div class="section-header">
          <v-icon size="16">mdi-text-box-outline</v-icon>
          <span>Logs</span>
          <LTag v-if="logMode === 'container' && activeLogContainerName" variant="accent" size="small" class="ml-2">
            {{ activeLogContainerName }}
          </LTag>
          <div class="header-controls">
            <!-- Desktop controls -->
            <template v-if="!isMobile">
              <v-select v-model="logMode" :items="logModeOptions" variant="outlined" density="compact" hide-details class="log-field" />
              <v-select v-model="logContainerId" :items="containerOptions" variant="outlined" density="compact" hide-details :disabled="logMode !== 'container'" class="log-field log-field--wide" />
              <v-text-field v-model.number="logTail" type="number" label="Tail" variant="outlined" density="compact" hide-details min="0" max="5000" class="log-field log-field--small" />
            </template>
            <LTag v-if="logsPaused" variant="warning" size="small">{{ isMobile ? '' : 'pausiert' }}</LTag>
            <LBtn :icon="isMobile" :prepend-icon="!isMobile ? (logsPaused ? 'mdi-play' : 'mdi-pause') : ''" variant="tonal" size="small" @click="toggleLogsPause">
              <v-icon v-if="isMobile">{{ logsPaused ? 'mdi-play' : 'mdi-pause' }}</v-icon>
              <template v-else>{{ logsPaused ? 'Live' : 'Pause' }}</template>
            </LBtn>
            <LBtn v-if="!isMobile" prepend-icon="mdi-trash-can-outline" variant="tonal" size="small" @click="clearLogs">
              Leeren
            </LBtn>
            <LBtn :icon="isMobile" :prepend-icon="!isMobile ? 'mdi-connection' : ''" variant="primary" size="small" @click="resubscribeLogs">
              <v-icon v-if="isMobile">mdi-connection</v-icon>
              <template v-else>Verbinden</template>
            </LBtn>
          </div>
        </div>
        <div ref="logsEl" class="logs-container">
          <div v-if="isLoading('logs')" class="logs-skeleton">
            <div v-for="n in 14" :key="'log-skel-' + n" class="logs-skeleton-line"></div>
          </div>
          <div v-else-if="!formattedLogHtml" class="logs-empty">
            <v-icon size="20">mdi-text-box-outline</v-icon>
            <span>Keine Logs (noch)</span>
          </div>
          <div v-else class="logs-content" v-html="formattedLogHtml"></div>
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
import { useMobile } from '@/composables/useMobile'

const socketioEnableWebsocket = String(import.meta.env.VITE_SOCKETIO_ENABLE_WEBSOCKET || '').toLowerCase() === 'true'
const socketioTransports = socketioEnableWebsocket ? ['polling', 'websocket'] : ['polling']

const auth = useAuth()
const { isLoading, setLoading } = useSkeletonLoading(['summary', 'charts', 'table', 'logs'])
const { isMobile } = useMobile()

// Staggered loading delays (ms) - sections appear one after another
const STAGGER_DELAYS = {
  summary: 0,
  charts: 150,
  table: 300,
  logs: 450
}

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
const lastNetSampleAtMs = ref(null)
const netRxRate = ref(0)
const netTxRate = ref(0)
const netRxRateHistory = ref([])
const netTxRateHistory = ref([])

const socket = ref(null)

// Track if logs have been auto-subscribed
const logsAutoSubscribed = ref(false)
const hasReceivedFirstStats = ref(false)

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

// Staggered loading - show sections one after another
const staggeredLoadingTimers = {}

const setStaggeredLoading = (sections, loading) => {
  // Clear any pending timers
  Object.values(staggeredLoadingTimers).forEach(timer => clearTimeout(timer))

  if (loading) {
    // When setting to loading, do it immediately
    sections.forEach(section => setLoading(section, true))
  } else {
    // When removing loading, stagger the removal for progressive appearance
    sections.forEach(section => {
      const delay = STAGGER_DELAYS[section] || 0
      staggeredLoadingTimers[section] = setTimeout(() => {
        setLoading(section, false)
      }, delay)
    })
  }
}

const clearStaggeredTimers = () => {
  Object.values(staggeredLoadingTimers).forEach(timer => clearTimeout(timer))
}

const resubscribeStats = () => {
  if (!socket.value) return
  // Set all stats-related sections to loading immediately
  setStaggeredLoading(['summary', 'charts', 'table'], true)
  socket.value.emit('docker:unsubscribe_stats', { scope: 'project' })
  socket.value.emit('docker:unsubscribe_stats', { scope: 'all' })
  socket.value.emit('docker:subscribe_stats', { scope: scope.value })
}

// Logs
const logsEl = ref(null)
const logsPaused = ref(false)
const autoScroll = ref(true)
const formattedLogHtml = ref('')
let _formattedLogLines = []

const LOG_FLUSH_INTERVAL_MS = 250
const MAX_PENDING_LOG_LINES = 5000
const _pendingLogLines = []
let logFlushTimer = null

const logModeOptions = [{ title: 'System', value: 'system' }, { title: 'Container', value: 'container' }]
const logMode = ref('container')
const logScope = ref('project')
const logContainerId = ref(null)
const logTail = ref(200)

const containerOptions = computed(() => (containers.value || []).map((c) => ({ title: c.name, value: c.id })))

const activeLogContainerName = computed(() => {
  if (logMode.value !== 'container' || !logContainerId.value) return null
  const c = containers.value.find(c => c.id === logContainerId.value)
  return c?.name || null
})

// ANSI color parsing
const ANSI_COLORS = {
  30: '#4a4a4a', 31: '#e8a087', 32: '#98d4bb', 33: '#e8c87a',
  34: '#a8c5e2', 35: '#c9a8e2', 36: '#88c4c8', 37: '#e0e0e0',
  90: '#6a6a6a', 91: '#ff9b8a', 92: '#a8e4cb', 93: '#f8d88a',
  94: '#b8d5f2', 95: '#d9b8f2', 96: '#98d4d8', 97: '#f0f0f0'
}

const BG_COLORS = {
  40: '#4a4a4a', 41: '#e8a087', 42: '#98d4bb', 43: '#e8c87a',
  44: '#a8c5e2', 45: '#c9a8e2', 46: '#88c4c8', 47: '#e0e0e0',
  100: '#6a6a6a', 101: '#ff9b8a', 102: '#a8e4cb', 103: '#f8d88a',
  104: '#b8d5f2', 105: '#d9b8f2', 106: '#98d4d8', 107: '#f0f0f0'
}

const escapeHtml = (text) => {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

const parseAnsiLine = (line) => {
  const ansiRegex = /\x1b\[([0-9;]*)m/g
  let result = ''
  let lastIndex = 0
  let currentStyles = []
  let match

  while ((match = ansiRegex.exec(line)) !== null) {
    if (match.index > lastIndex) {
      const text = escapeHtml(line.slice(lastIndex, match.index))
      if (currentStyles.length > 0) {
        result += `<span style="${currentStyles.join(';')}">${text}</span>`
      } else {
        result += text
      }
    }

    const codes = match[1].split(';').map(c => parseInt(c, 10) || 0)
    for (const code of codes) {
      if (code === 0) {
        currentStyles = []
      } else if (code === 1) {
        currentStyles.push('font-weight:bold')
      } else if (code === 2) {
        currentStyles.push('opacity:0.7')
      } else if (code === 3) {
        currentStyles.push('font-style:italic')
      } else if (code === 4) {
        currentStyles.push('text-decoration:underline')
      } else if (ANSI_COLORS[code]) {
        currentStyles.push(`color:${ANSI_COLORS[code]}`)
      } else if (BG_COLORS[code]) {
        currentStyles.push(`background-color:${BG_COLORS[code]}`)
      }
    }

    lastIndex = ansiRegex.lastIndex
  }

  if (lastIndex < line.length) {
    const text = escapeHtml(line.slice(lastIndex))
    if (currentStyles.length > 0) {
      result += `<span style="${currentStyles.join(';')}">${text}</span>`
    } else {
      result += text
    }
  }

  return result || escapeHtml(line)
}

const applyLogLevelColors = (line) => {
  if (/\b(ERROR|FATAL|CRITICAL)\b/i.test(line)) {
    return `<span class="log-error">${line}</span>`
  }
  if (/\b(WARN|WARNING)\b/i.test(line)) {
    return `<span class="log-warn">${line}</span>`
  }
  if (/\b(INFO)\b/i.test(line)) {
    return `<span class="log-info">${line}</span>`
  }
  if (/\b(DEBUG|TRACE)\b/i.test(line)) {
    return `<span class="log-debug">${line}</span>`
  }
  return line
}

const LOG_TRIM_BUFFER = 300

const formatLogLine = (line) => {
  const raw = String(line || '')
  let parsed = parseAnsiLine(raw)
  if (!raw.includes('\x1b[')) {
    parsed = applyLogLevelColors(parsed)
  }
  return parsed
}

const clearLogs = () => {
  formattedLogHtml.value = ''
  _pendingLogLines.length = 0
  _formattedLogLines = []
}

const toggleLogsPause = () => { logsPaused.value = !logsPaused.value }

const scrollLogsToBottom = () => {
  if (!autoScroll.value) return
  const el = logsEl.value
  if (!el) return
  requestAnimationFrame(() => { el.scrollTop = el.scrollHeight })
}

const flushLogs = () => {
  if (_pendingLogLines.length === 0) return
  const newLines = _pendingLogLines.splice(0, _pendingLogLines.length)
  const formatted = newLines.map(formatLogLine)
  _formattedLogLines.push(...formatted)

  const chunk = formatted.join('\n')
  formattedLogHtml.value = formattedLogHtml.value ? `${formattedLogHtml.value}\n${chunk}` : chunk

  // Avoid rebuilding the whole HTML string on every flush: trim in larger chunks
  if (_formattedLogLines.length > (MAX_LOG_LINES + LOG_TRIM_BUFFER)) {
    _formattedLogLines.splice(0, _formattedLogLines.length - MAX_LOG_LINES)
    formattedLogHtml.value = _formattedLogLines.join('\n')
  }

  if (isLoading('logs')) setLoading('logs', false)
  scrollLogsToBottom()
}

const scheduleFlushLogs = () => {
  if (logFlushTimer) return
  logFlushTimer = setTimeout(() => { logFlushTimer = null; flushLogs() }, LOG_FLUSH_INTERVAL_MS)
}

const resubscribeLogs = () => {
  if (!socket.value) return
  const payload = { mode: logMode.value, scope: logScope.value, tail: Math.max(0, Math.min(5000, Number(logTail.value || 0))) }
  if (logMode.value === 'container') {
    if (!logContainerId.value) {
      const first = containerOptions.value?.[0]?.value
      if (first) logContainerId.value = first
    }
    if (!logContainerId.value) {
      errorMessage.value = 'Kein Container verfügbar'
      setLoading('logs', false)
      return
    }
    payload.container_id = logContainerId.value
  }
  setLoading('logs', true)
  errorMessage.value = ''
  socket.value.emit('docker:unsubscribe_logs')
  socket.value.emit('docker:subscribe_logs', payload)
}

const switchToContainerLogs = (container) => {
  clearLogs()
  logMode.value = 'container'
  logContainerId.value = container.id
  setTimeout(() => { resubscribeLogs() }, 50)
}

const connectSocket = () => {
  const token = auth.getToken()
  if (!token) {
    connectionState.value = 'error'
    errorMessage.value = 'Kein Auth-Token gefunden.'
    setLoading('summary', false); setLoading('charts', false); setLoading('table', false); setLoading('logs', false)
    return
  }

  errorMessage.value = ''
  connectionState.value = 'connecting'
  // Set all sections to loading immediately
  setStaggeredLoading(['summary', 'charts', 'table'], true)
  setLoading('logs', true)
  hasReceivedFirstStats.value = false
  logsAutoSubscribed.value = false

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

  s.on('connect', () => {
    connectionState.value = 'connected'
    resubscribeStats()
  })

  s.on('disconnect', () => { connectionState.value = 'disconnected' })
  s.on('connect_error', (err) => {
    connectionState.value = 'error'
    errorMessage.value = err?.message || 'Socket Verbindung fehlgeschlagen'
    setLoading('summary', false); setLoading('charts', false); setLoading('table', false); setLoading('logs', false)
  })

  s.on('docker:error', (payload) => {
    errorMessage.value = payload?.message || 'Docker Fehler'
    setLoading('summary', false); setLoading('charts', false); setLoading('table', false); setLoading('logs', false)
  })

  s.on('docker:stats', (payload) => {
    if (!payload?.ok) {
      errorMessage.value = payload?.error || 'Docker Snapshot fehlgeschlagen'
      // On error, remove loading immediately without staggering
      setLoading('summary', false); setLoading('charts', false); setLoading('table', false)
      return
    }

    errorMessage.value = ''
    containers.value = Array.isArray(payload.containers) ? payload.containers : []
    const newSummary = payload.summary || summary.value
    summary.value = newSummary

    // Use staggered loading - sections appear one after another
    setStaggeredLoading(['summary', 'charts', 'table'], false)

    pushHistoryPoint(summaryCpuHistory, newSummary.cpu_total_percent)
    pushHistoryPoint(summaryMemHistory, newSummary.mem_total_bytes)

    const currentNetRx = newSummary.net_rx_bytes || 0
    const currentNetTx = newSummary.net_tx_bytes || 0

    const nowMs = Date.now()
    const deltaSec = lastNetSampleAtMs.value ? Math.max(0.001, (nowMs - lastNetSampleAtMs.value) / 1000) : null
    if (deltaSec && lastNetRx.value > 0 && currentNetRx >= lastNetRx.value) {
      netRxRate.value = (currentNetRx - lastNetRx.value) / deltaSec
    } else if (!deltaSec) {
      netRxRate.value = 0
    }
    if (deltaSec && lastNetTx.value > 0 && currentNetTx >= lastNetTx.value) {
      netTxRate.value = (currentNetTx - lastNetTx.value) / deltaSec
    } else if (!deltaSec) {
      netTxRate.value = 0
    }

    lastNetRx.value = currentNetRx
    lastNetTx.value = currentNetTx
    lastNetSampleAtMs.value = nowMs

    pushHistoryPoint(netRxRateHistory, bytesToKiB(netRxRate.value))
    pushHistoryPoint(netTxRateHistory, bytesToKiB(netTxRate.value))
    pushHistoryPoint(summaryNetRxHistory, currentNetRx)
    pushHistoryPoint(summaryNetTxHistory, currentNetTx)

    if (logMode.value === 'container' && logContainerId.value) {
      const exists = containers.value.some((c) => c.id === logContainerId.value)
      if (!exists) logContainerId.value = null
    }

    if (!hasReceivedFirstStats.value) {
      hasReceivedFirstStats.value = true
      if (!logsAutoSubscribed.value) {
        logsAutoSubscribed.value = true
        resubscribeLogs()
      }
    }
  })

  s.on('docker:logs_subscribed', () => {
    if (isLoading('logs')) setLoading('logs', false)
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

onBeforeUnmount(() => {
  if (logFlushTimer) { clearTimeout(logFlushTimer); logFlushTimer = null }
  clearStaggeredTimers()
  disconnectSocket()
})

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
      const padding = { top: 4, right: 4, bottom: 12, left: 28 }
      const chartW = w - padding.left - padding.right
      const chartH = h - padding.top - padding.bottom

      ctx.clearRect(0, 0, w, h)

      const vals = props.values.slice(-props.maxPoints)
      if (vals.length < 2) {
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

      let minVal = props.minValue !== null ? props.minValue : Math.min(...vals)
      let maxVal = props.maxValue !== null ? props.maxValue : Math.max(...vals)
      if (minVal === maxVal) { minVal = minVal - 1; maxVal = maxVal + 1 }
      const range = maxVal - minVal

      ctx.strokeStyle = 'rgba(150, 150, 150, 0.15)'
      ctx.lineWidth = 1
      ctx.setLineDash([2, 2])
      const gridLines = 2
      for (let i = 0; i <= gridLines; i++) {
        const y = padding.top + (chartH / gridLines) * i
        ctx.beginPath()
        ctx.moveTo(padding.left, y)
        ctx.lineTo(w - padding.right, y)
        ctx.stroke()
      }
      ctx.setLineDash([])

      ctx.fillStyle = 'rgba(150, 150, 150, 0.7)'
      ctx.font = '8px system-ui, sans-serif'
      ctx.textAlign = 'right'
      ctx.textBaseline = 'middle'
      for (let i = 0; i <= gridLines; i++) {
        const y = padding.top + (chartH / gridLines) * i
        const value = maxVal - (range / gridLines) * i
        ctx.fillText(value.toFixed(value >= 100 ? 0 : 1), padding.left - 2, y)
      }

      const points = vals.map((v, idx) => {
        const x = padding.left + (idx / (props.maxPoints - 1)) * chartW
        const y = padding.top + chartH - ((v - minVal) / range) * chartH
        return { x, y }
      })

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

      ctx.beginPath()
      ctx.moveTo(points[0].x, points[0].y)
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

      if (points.length > 0) {
        const lastPoint = points[points.length - 1]
        ctx.beginPath()
        ctx.arc(lastPoint.x, lastPoint.y, 3, 0, Math.PI * 2)
        ctx.fillStyle = props.color
        ctx.fill()
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
  padding: 12px;
  gap: 10px;
}

/* Header */
.monitor-header {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: var(--llars-gradient-primary);
  border-radius: var(--llars-radius);
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  color: white;
}

.header-left h2 {
  margin: 0;
  font-size: 1rem;
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

@keyframes shimmer {
  0% { background-position: 100% 0; }
  100% { background-position: 0 0; }
}

.skeleton-line {
  display: inline-block;
  border-radius: 4px;
  background: linear-gradient(
    90deg,
    rgba(var(--v-theme-on-surface), 0.06) 25%,
    rgba(var(--v-theme-on-surface), 0.12) 37%,
    rgba(var(--v-theme-on-surface), 0.06) 63%
  );
  background-size: 400% 100%;
  animation: shimmer 1.2s ease-in-out infinite;
}

.skeleton-line--lg {
  height: 14px;
  width: 52%;
}

.skeleton-line--sm {
  height: 10px;
  width: 38%;
}

.skeleton-line--mono {
  height: 12px;
  width: 64px;
}

.chart-skeleton {
  height: 60px;
  border-radius: 6px;
  background: linear-gradient(
    90deg,
    rgba(var(--v-theme-on-surface), 0.05) 25%,
    rgba(var(--v-theme-on-surface), 0.10) 37%,
    rgba(var(--v-theme-on-surface), 0.05) 63%
  );
  background-size: 400% 100%;
  animation: shimmer 1.2s ease-in-out infinite;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.scope-select {
  width: 90px;
  background: rgba(255,255,255,0.15);
  border-radius: 6px;
}

.scope-select :deep(.v-field__outline) { border-color: rgba(255,255,255,0.3); }
.scope-select :deep(.v-field__input),
.scope-select :deep(.v-select__selection-text) { color: white; font-size: 0.8rem; }

/* Error Banner */
.error-banner {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: rgba(232, 160, 135, 0.15);
  border-left: 3px solid var(--llars-danger);
  border-radius: var(--llars-radius-xs);
  font-size: 0.8rem;
}

/* Main Content */
.monitor-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 0;
  overflow: hidden;
}

/* Top Section: Stats + Charts + Table */
.top-section {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Stats Row */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.stat-item {
  padding: 8px 6px;
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius-sm);
  text-align: center;
  box-shadow: var(--llars-shadow-sm);
}

.stat-item--success { background: rgba(152, 212, 187, 0.2); }
.stat-item--info { background: rgba(168, 197, 226, 0.2); }
.stat-item--danger { background: rgba(232, 160, 135, 0.2); }

.stat-item--skeleton {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.stat-value {
  display: block;
  font-size: 1rem;
  font-weight: 700;
}

.stat-label {
  font-size: 0.55rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Charts + Table Row */
.charts-table-row {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  flex: 1;
}

.chart-card {
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius-sm);
  padding: 8px;
  box-shadow: var(--llars-shadow-sm);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.7rem;
  font-weight: 600;
}

.chart-value {
  font-size: 0.8rem;
  font-weight: 700;
  font-family: 'SF Mono', 'Monaco', monospace;
}

.chart-value--primary { color: var(--llars-primary); }
.chart-value--accent { color: var(--llars-accent); }
.chart-value--info { color: var(--llars-info); }
.chart-value--warning { color: var(--llars-warning); }

.chart-container {
  height: 60px;
}

/* Table Section */
.table-section {
  width: 100%;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius-sm);
  box-shadow: var(--llars-shadow-sm);
  overflow: hidden;
}

.table-section .section-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 8px 10px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.table-skeleton {
  flex: 1;
  padding: 8px 10px 12px;
}

.table-wrapper {
  flex: 1;
  overflow: auto;
  max-height: 160px;
}

.container-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.75rem;
}

.container-table th {
  position: sticky;
  top: 0;
  background: rgba(var(--v-theme-on-surface), 0.03);
  padding: 6px 8px;
  text-align: left;
  font-weight: 600;
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.container-table td {
  padding: 5px 8px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.05);
}

.container-table tbody tr {
  transition: background-color 0.15s ease;
}

.container-table tbody tr:hover {
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.container-table tbody tr.selected {
  background: rgba(136, 196, 200, 0.2);
}

.name-cell {
  cursor: pointer;
}

.name-link {
  font-weight: 500;
  color: var(--llars-accent);
  transition: color 0.15s ease;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
  font-size: 0.7rem;
}

.name-link:hover {
  color: var(--llars-primary);
  text-decoration: underline;
}

.value-cell {
  font-family: 'SF Mono', monospace;
  font-size: 0.7rem;
}

/* Logs Section (full width, takes remaining space) */
.logs-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius-sm);
  box-shadow: var(--llars-shadow-sm);
  overflow: hidden;
}

.logs-section .section-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 8px 10px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-wrap: wrap;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  flex-wrap: wrap;
}

.log-field { width: 100px; }
.log-field--wide { width: 140px; }
.log-field--small { width: 60px; }

.logs-container {
  flex: 1;
  min-height: 0;
  overflow: auto;
  background: rgba(20, 20, 25, 0.98);
  margin: 6px;
  border-radius: var(--llars-radius-xs);
}

.logs-skeleton {
  padding: 10px 10px 14px;
}

.logs-skeleton-line {
  height: 10px;
  margin: 7px 0;
  border-radius: 4px;
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.06) 25%,
    rgba(255, 255, 255, 0.12) 37%,
    rgba(255, 255, 255, 0.06) 63%
  );
  background-size: 400% 100%;
  animation: shimmer 1.2s ease-in-out infinite;
}

.logs-skeleton-line:nth-child(3n) { width: 92%; }
.logs-skeleton-line:nth-child(3n+1) { width: 74%; }
.logs-skeleton-line:nth-child(3n+2) { width: 60%; }

.logs-empty {
  height: 100%;
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.65);
}

.logs-content {
  margin: 0;
  padding: 8px;
  font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace;
  font-size: 0.7rem;
  line-height: 1.4;
  color: #d0d0d0;
  white-space: pre;
}

/* Log level colors */
.logs-content :deep(.log-error) { color: #ff9b8a; }
.logs-content :deep(.log-warn) { color: #f8d88a; }
.logs-content :deep(.log-info) { color: #a8d5f2; }
.logs-content :deep(.log-debug) { color: #888; }

/* Chart Canvas */
.live-chart-canvas {
  display: block;
}

/* Scrollbars */
.table-wrapper::-webkit-scrollbar,
.logs-container::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.table-wrapper::-webkit-scrollbar-track { background: transparent; }
.table-wrapper::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 3px;
}

.logs-container::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
.logs-container::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.15);
  border-radius: 3px;
}

/* Responsive */
@media (max-width: 1200px) {
  .charts-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .table-wrapper {
    max-height: 100px;
  }
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }
}

/* ============================================
   MOBILE RESPONSIVE STYLES
   ============================================ */
.docker-monitor.is-mobile {
  padding: 8px;
  gap: 8px;
  overflow: hidden;
  max-width: 100vw;
}

.docker-monitor.is-mobile .monitor-header {
  padding: 8px 12px;
  gap: 8px;
}

.docker-monitor.is-mobile .monitor-header h2 {
  font-size: 0.9rem;
}

.docker-monitor.is-mobile .stats-row {
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.docker-monitor.is-mobile .stat-item {
  padding: 6px 4px;
}

.docker-monitor.is-mobile .stat-value {
  font-size: 0.9rem;
}

.docker-monitor.is-mobile .stat-label {
  font-size: 0.5rem;
}

.docker-monitor.is-mobile .table-wrapper {
  max-height: 120px;
}

.docker-monitor.is-mobile .container-table {
  font-size: 0.7rem;
}

.docker-monitor.is-mobile .container-table th,
.docker-monitor.is-mobile .container-table td {
  padding: 4px 6px;
}

.docker-monitor.is-mobile .name-link {
  max-width: 120px;
  font-size: 0.65rem;
}

.docker-monitor.is-mobile .section-header {
  padding: 6px 8px;
  font-size: 0.7rem;
}

.docker-monitor.is-mobile .header-controls {
  gap: 4px;
}

.docker-monitor.is-mobile .logs-container {
  margin: 4px;
}

.docker-monitor.is-mobile .logs-content {
  font-size: 0.6rem;
  padding: 6px;
}

.docker-monitor.is-mobile .error-banner {
  padding: 4px 8px;
  font-size: 0.7rem;
}
</style>
