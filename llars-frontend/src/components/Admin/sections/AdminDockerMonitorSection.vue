<template>
  <div class="docker-monitor">
    <v-row>
      <v-col cols="12" md="4">
        <v-skeleton-loader
          v-if="isLoading('summary')"
          type="card, paragraph, actions"
          height="260"
          class="mb-4"
        />

        <v-card v-else class="mb-4">
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-docker</v-icon>
            Docker Monitor
            <v-spacer />

            <v-chip
              :color="connectionColor"
              variant="tonal"
              density="compact"
              class="mr-2"
            >
              <v-icon start size="16">{{ connectionIcon }}</v-icon>
              {{ connectionLabel }}
            </v-chip>

            <LBtn
              prepend-icon="mdi-refresh"
              variant="tonal"
              density="comfortable"
              @click="resubscribeStats"
            >
              Refresh
            </LBtn>
          </v-card-title>
          <v-divider />
          <v-card-text>
            <v-alert
              v-if="errorMessage"
              type="error"
              variant="tonal"
              density="compact"
              class="mb-3"
            >
              {{ errorMessage }}
            </v-alert>

            <v-select
              v-model="scope"
              :items="scopeOptions"
              label="Scope"
              variant="outlined"
              density="comfortable"
              hide-details
              class="mb-3"
            />

            <div class="d-flex flex-wrap ga-2">
              <v-chip variant="tonal" density="compact">
                Total: {{ summary.total }}
              </v-chip>
              <v-chip color="success" variant="tonal" density="compact">
                Running: {{ summary.running }}
              </v-chip>
              <v-chip color="info" variant="tonal" density="compact">
                Exited: {{ summary.exited }}
              </v-chip>
              <v-chip :color="summary.unhealthy > 0 ? 'error' : 'success'" variant="tonal" density="compact">
                Healthy: {{ summary.healthy }}/{{ summary.total }}
              </v-chip>
              <v-chip v-if="summary.no_healthcheck > 0" color="warning" variant="tonal" density="compact">
                No HC: {{ summary.no_healthcheck }}
              </v-chip>
            </div>

            <v-divider class="my-4" />

            <div class="text-subtitle-2 font-weight-medium mb-2">Ressourcen (gesamt)</div>
            <div class="d-flex align-center justify-space-between">
              <div class="text-body-2 text-medium-emphasis">CPU</div>
              <div class="text-body-2 font-weight-medium">{{ formatPercent(summary.cpu_total_percent) }}</div>
            </div>
            <MiniSparkline :values="summaryCpuHistory" class="mb-3" color="primary" />

            <div class="d-flex align-center justify-space-between">
              <div class="text-body-2 text-medium-emphasis">RAM</div>
              <div class="text-body-2 font-weight-medium">{{ formatBytes(summary.mem_total_bytes) }}</div>
            </div>
            <MiniSparkline :values="summaryMemHistoryMiB" color="secondary" />
          </v-card-text>
        </v-card>

        <v-skeleton-loader
          v-if="isLoading('detail')"
          type="card"
          height="220"
        />

        <v-card v-else>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-chart-line</v-icon>
            Container Detail
            <v-spacer />
            <v-chip v-if="selectedContainer" density="compact" variant="tonal">
              {{ selectedContainer.name }}
            </v-chip>
          </v-card-title>
          <v-divider />
          <v-card-text>
            <v-alert
              v-if="!selectedContainer"
              type="info"
              variant="tonal"
              density="compact"
            >
              Wähle einen Container aus der Liste.
            </v-alert>

            <template v-else>
              <div class="d-flex align-center justify-space-between">
                <div class="text-body-2 text-medium-emphasis">CPU</div>
                <div class="text-body-2 font-weight-medium">{{ formatPercent(selectedContainer.cpu_percent) }}</div>
              </div>
              <MiniSparkline :values="selectedCpuHistory" class="mb-3" color="primary" />

              <div class="d-flex align-center justify-space-between">
                <div class="text-body-2 text-medium-emphasis">RAM</div>
                <div class="text-body-2 font-weight-medium">
                  {{ formatBytes(selectedContainer.mem_usage) }}
                  <span v-if="selectedContainer.mem_limit" class="text-medium-emphasis">
                    / {{ formatBytes(selectedContainer.mem_limit) }}
                  </span>
                </div>
              </div>
              <MiniSparkline :values="selectedMemHistoryMiB" color="secondary" />
            </template>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="8">
        <v-card class="mb-4">
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-view-list</v-icon>
            Container
            <v-spacer />
            <v-chip variant="tonal" density="compact">
              {{ containers.length }} Einträge
            </v-chip>
          </v-card-title>
          <v-divider />
          <v-card-text>
            <v-skeleton-loader v-if="isLoading('table')" type="table" height="360" />

            <v-data-table
              v-else
              :headers="tableHeaders"
              :items="containers"
              item-key="id"
              density="comfortable"
              :items-per-page="15"
              fixed-header
              height="420"
              class="docker-table"
              @click:row="(event, { item }) => selectContainer(item)"
              :row-props="rowProps"
            >
              <template v-slot:item.state="{ item }">
                <v-chip :color="stateColor(item.state)" variant="tonal" density="compact">
                  {{ item.state }}
                </v-chip>
              </template>

              <template v-slot:item.health="{ item }">
                <v-chip :color="healthColor(item.health)" variant="tonal" density="compact">
                  {{ item.health || '—' }}
                </v-chip>
              </template>

              <template v-slot:item.cpu_percent="{ item }">
                <span class="font-weight-medium">{{ formatPercent(item.cpu_percent) }}</span>
              </template>

              <template v-slot:item.mem="{ item }">
                <span class="font-weight-medium">
                  {{ formatPercent(item.mem_percent) }}
                </span>
                <span class="text-caption text-medium-emphasis">
                  ({{ formatBytes(item.mem_usage) }})
                </span>
              </template>

              <template v-slot:no-data>
                <v-alert type="info" variant="tonal" density="compact">
                  Keine Container gefunden.
                </v-alert>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>

        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-text-box-outline</v-icon>
            Logs
            <v-spacer />

            <v-chip v-if="logsPaused" color="grey" variant="tonal" density="compact" class="mr-2">
              pausiert
            </v-chip>

            <LBtn
              :prepend-icon="logsPaused ? 'mdi-play' : 'mdi-pause'"
              variant="tonal"
              class="mr-2"
              @click="toggleLogsPause"
            >
              {{ logsPaused ? 'Live' : 'Pause' }}
            </LBtn>

            <LBtn
              prepend-icon="mdi-trash-can-outline"
              variant="tonal"
              @click="clearLogs"
            >
              Leeren
            </LBtn>
          </v-card-title>
          <v-divider />
          <v-card-text>
            <v-row>
              <v-col cols="12" md="4">
                <v-select
                  v-model="logMode"
                  :items="logModeOptions"
                  label="Modus"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-select
                  v-model="logScope"
                  :items="scopeOptions"
                  label="Scope"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-select
                  v-model="logContainerId"
                  :items="containerOptions"
                  label="Container"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  :disabled="logMode !== 'container'"
                />
              </v-col>
            </v-row>

            <v-row class="mt-1">
              <v-col cols="12" md="4">
                <v-text-field
                  v-model.number="logTail"
                  type="number"
                  label="Tail"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  min="0"
                  max="5000"
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-switch
                  v-model="autoScroll"
                  color="primary"
                  hide-details
                  label="Auto-Scroll"
                />
              </v-col>
              <v-col cols="12" md="4" class="d-flex align-center justify-end">
                <LBtn
                  prepend-icon="mdi-sync"
                  variant="primary"
                  @click="resubscribeLogs"
                >
                  Verbinden
                </LBtn>
              </v-col>
            </v-row>

            <div ref="logsEl" class="logs mt-3">
              <pre class="logs__pre">{{ logText }}</pre>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { io } from 'socket.io-client'
import { useAuth } from '@/composables/useAuth'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'

const auth = useAuth()
const { isLoading, setLoading } = useSkeletonLoading(['summary', 'table', 'detail'])

const MAX_POINTS = 120
const MAX_LOG_LINES = 2000

const connectionState = ref('disconnected') // disconnected|connecting|connected|error
const errorMessage = ref('')

const scopeOptions = [
  { title: 'LLARS (Project)', value: 'project' },
  { title: 'Alle Container', value: 'all' }
]

const scope = ref('project')

const containers = ref([])
const summary = ref({
  total: 0,
  running: 0,
  exited: 0,
  restarting: 0,
  paused: 0,
  healthy: 0,
  unhealthy: 0,
  starting: 0,
  no_healthcheck: 0,
  cpu_total_percent: 0,
  mem_total_bytes: 0
})

const summaryCpuHistory = ref([])
const summaryMemHistory = ref([])

const selectedContainerId = ref(null)
const selectedCpuHistory = ref([])
const selectedMemHistory = ref([])

const tableHeaders = [
  { title: 'Name', key: 'name', sortable: true },
  { title: 'State', key: 'state', sortable: true, width: 120 },
  { title: 'Health', key: 'health', sortable: true, width: 140 },
  { title: 'CPU', key: 'cpu_percent', sortable: true, width: 120 },
  { title: 'RAM', key: 'mem', sortable: false }
]

const socket = ref(null)

const connectionLabel = computed(() => {
  if (connectionState.value === 'connected') return 'live'
  if (connectionState.value === 'connecting') return 'verbinde...'
  if (connectionState.value === 'error') return 'fehler'
  return 'offline'
})

const connectionColor = computed(() => {
  if (connectionState.value === 'connected') return 'success'
  if (connectionState.value === 'connecting') return 'warning'
  if (connectionState.value === 'error') return 'error'
  return 'grey'
})

const connectionIcon = computed(() => {
  if (connectionState.value === 'connected') return 'mdi-wifi'
  if (connectionState.value === 'connecting') return 'mdi-wifi-sync'
  if (connectionState.value === 'error') return 'mdi-wifi-off'
  return 'mdi-wifi-off'
})

const formatPercent = (value) => `${Number(value || 0).toFixed(2)}%`

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

const stateColor = (state) => {
  const s = String(state || '').toLowerCase()
  if (s === 'running') return 'success'
  if (s === 'exited') return 'info'
  if (s === 'restarting') return 'warning'
  return 'grey'
}

const healthColor = (health) => {
  const h = String(health || '').toLowerCase()
  if (h === 'healthy') return 'success'
  if (h === 'unhealthy') return 'error'
  if (h === 'starting') return 'warning'
  return 'grey'
}

const rowProps = ({ item }) => {
  if (!item) return {}
  return { class: item.id === selectedContainerId.value ? 'selected-row' : '' }
}

const pushHistoryPoint = (arrRef, value) => {
  arrRef.value.push(Number(value || 0))
  if (arrRef.value.length > MAX_POINTS) {
    arrRef.value.splice(0, arrRef.value.length - MAX_POINTS)
  }
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
    return
  }

  errorMessage.value = ''
  connectionState.value = 'connecting'

  const rawBaseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin
  const baseUrl = String(rawBaseUrl || '').replace(/\/+$/, '')
  const s = io(`${baseUrl}/admin`, {
    path: '/socket.io',
    transports: ['websocket', 'polling'],
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
    resubscribeLogs()
  })

  s.on('disconnect', () => {
    connectionState.value = 'disconnected'
  })

  s.on('connect_error', (err) => {
    connectionState.value = 'error'
    errorMessage.value = err?.message || 'Socket Verbindung fehlgeschlagen'
  })

  s.on('docker:error', (payload) => {
    const message = payload?.message || 'Docker Fehler'
    errorMessage.value = message
  })

  s.on('docker:stats', (payload) => {
    if (!payload?.ok) {
      errorMessage.value = payload?.error || 'Docker Snapshot fehlgeschlagen'
      return
    }

    errorMessage.value = ''
    containers.value = Array.isArray(payload.containers) ? payload.containers : []
    summary.value = payload.summary || summary.value

    setLoading('summary', false)
    setLoading('table', false)
    setLoading('detail', false)

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
  } catch (e) {
    // ignore
  }
  socket.value?.disconnect()
  socket.value = null
}

// Logs
const logsEl = ref(null)
const logsPaused = ref(false)
const autoScroll = ref(true)
const logLines = ref([])

const logModeOptions = [
  { title: 'System (alle Logs)', value: 'system' },
  { title: 'Container', value: 'container' }
]
const logMode = ref('system')
const logScope = ref('project')
const logContainerId = ref(null)
const logTail = ref(200)

const containerOptions = computed(() => {
  return (containers.value || []).map((c) => ({ title: c.name, value: c.id }))
})

const logText = computed(() => logLines.value.join('\n'))

const clearLogs = () => {
  logLines.value = []
}

const toggleLogsPause = () => {
  logsPaused.value = !logsPaused.value
}

const scrollLogsToBottom = () => {
  if (!autoScroll.value) return
  const el = logsEl.value
  if (!el) return
  requestAnimationFrame(() => {
    el.scrollTop = el.scrollHeight
  })
}

const resubscribeLogs = () => {
  if (!socket.value) return
  socket.value.emit('docker:unsubscribe_logs')

  const payload = {
    mode: logMode.value,
    scope: logScope.value,
    tail: Math.max(0, Math.min(5000, Number(logTail.value || 0)))
  }

  if (logMode.value === 'container') {
    if (!logContainerId.value) {
      errorMessage.value = 'Bitte Container auswählen'
      return
    }
    payload.container_id = logContainerId.value
  }

  errorMessage.value = ''
  socket.value.emit('docker:subscribe_logs', payload)
}

watch(scope, (newScope) => {
  if (logScope.value === 'project' || logScope.value === 'all') {
    // keep stats + logs in sync by default
    logScope.value = newScope
  }
  resubscribeStats()
})

watch(logMode, () => {
  if (logMode.value !== 'container') logContainerId.value = null
})

onMounted(() => {
  connectSocket()

  // Set default container selection for logs
  watch(
    containerOptions,
    (opts) => {
      if (logMode.value === 'container' && !logContainerId.value && opts.length > 0) {
        logContainerId.value = opts[0].value
      }
    },
    { immediate: true }
  )

  // Attach log line handler after socket creation
  const attachLogHandlers = () => {
    if (!socket.value) return
    socket.value.off('docker:log_line')
    socket.value.on('docker:log_line', (payload) => {
      if (logsPaused.value) return
      const cname = payload?.container_name ? `[${payload.container_name}] ` : ''
      const line = String(payload?.line || '')
      logLines.value.push(`${cname}${line}`)
      if (logLines.value.length > MAX_LOG_LINES) {
        logLines.value.splice(0, logLines.value.length - MAX_LOG_LINES)
      }
      scrollLogsToBottom()
    })
  }

  const stop = watch(socket, () => attachLogHandlers(), { immediate: true })

  onBeforeUnmount(() => {
    stop()
  })
})

onBeforeUnmount(() => {
  disconnectSocket()
})

const MiniSparkline = defineComponent({
  name: 'MiniSparkline',
  props: {
    values: { type: Array, default: () => [] },
    color: { type: String, default: 'primary' },
    height: { type: Number, default: 42 }
  },
  setup(props) {
    const points = computed(() => {
      const vals = (props.values || []).map((v) => Number(v || 0))
      if (vals.length < 2) return ''

      const w = 220
      const h = Number(props.height || 42)
      const min = Math.min(...vals)
      const max = Math.max(...vals)
      const span = max - min || 1

      return vals
        .map((v, idx) => {
          const x = (idx / (vals.length - 1)) * w
          const y = h - ((v - min) / span) * h
          return `${x.toFixed(1)},${y.toFixed(1)}`
        })
        .join(' ')
    })

    return () => {
      const w = 220
      const hVal = Number(props.height || 42)
      return h(
        'svg',
        {
          height: hVal,
          viewBox: `0 0 ${w} ${hVal}`,
          class: 'sparkline',
          preserveAspectRatio: 'none'
        },
        points.value
          ? [
              h('polyline', {
                points: points.value,
                class: ['sparkline__line', `sparkline__line--${props.color}`]
              })
            ]
          : [
              h('line', {
                x1: 0,
                y1: hVal / 2,
                x2: w,
                y2: hVal / 2,
                class: 'sparkline__empty'
              })
            ]
      )
    }
  }
})
</script>

<style scoped>
.logs {
  height: 360px;
  overflow: auto;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 8px;
  background: rgba(var(--v-theme-surface-variant), 0.15);
}

.logs__pre {
  margin: 0;
  padding: 12px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 12px;
  line-height: 1.4;
  color: rgb(var(--v-theme-on-surface));
  white-space: pre;
}

.docker-table :deep(tbody tr) {
  cursor: pointer;
}

.docker-table :deep(tbody tr.selected-row) {
  background: rgba(var(--v-theme-primary), 0.06);
}

.sparkline {
  width: 100%;
}

.sparkline__line {
  fill: none;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.sparkline__line--primary {
  stroke: rgb(var(--v-theme-primary));
}

.sparkline__line--secondary {
  stroke: rgb(var(--v-theme-secondary));
}

.sparkline__empty {
  stroke: rgba(var(--v-theme-on-surface), 0.2);
  stroke-width: 1;
}
</style>
