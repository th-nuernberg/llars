<template>
  <div class="health-bar" :class="{ 'health-bar--loading': loading }">
    <div class="health-bar__header">
      <span class="health-bar__title">
        <LIcon icon="mdi-heart-pulse" size="16" class="mr-1" />
        System Health
      </span>
      <LTag
        v-if="!loading && connected"
        variant="success"
        size="sm"
        prepend-icon="mdi-circle-small"
        class="health-bar__live"
      >
        Live
      </LTag>
    </div>

    <div class="health-bar__items">
      <!-- Host -->
      <div class="health-item" @click="navigateTo('health')">
        <div class="health-item__icon" :style="{ backgroundColor: getColorBg('host'), color: getColor('host') }">
          <LIcon icon="mdi-server" size="18" />
        </div>
        <div class="health-item__content">
          <span class="health-item__label">Host</span>
          <span class="health-item__value">{{ cpuPercent }}% CPU</span>
        </div>
        <div class="health-item__indicator">
          <span
            v-for="i in 5"
            :key="i"
            class="health-dot"
            :class="{ active: cpuPercent >= (i - 1) * 20 }"
            :style="{ backgroundColor: cpuPercent >= (i - 1) * 20 ? getColor('host') : undefined }"
          />
        </div>
      </div>

      <!-- API -->
      <div class="health-item" @click="navigateTo('health')">
        <div class="health-item__icon" :style="{ backgroundColor: getColorBg('api'), color: getColor('api') }">
          <LIcon icon="mdi-api" size="18" />
        </div>
        <div class="health-item__content">
          <span class="health-item__label">API</span>
          <span class="health-item__value">{{ requestsPerSec }}/s</span>
        </div>
        <div class="health-item__sub">{{ avgLatency }}ms</div>
      </div>

      <!-- WebSocket -->
      <div class="health-item" @click="navigateTo('health')">
        <div class="health-item__icon" :style="{ backgroundColor: getColorBg('ws'), color: getColor('ws') }">
          <LIcon icon="mdi-connection" size="18" />
        </div>
        <div class="health-item__content">
          <span class="health-item__label">WebSocket</span>
          <span class="health-item__value">{{ wsConnections }}</span>
        </div>
        <div class="health-item__sub">conns</div>
      </div>

      <!-- Docker -->
      <div class="health-item" @click="navigateTo('docker')">
        <div class="health-item__icon" :style="{ backgroundColor: getColorBg('docker'), color: getColor('docker') }">
          <LIcon icon="mdi-docker" size="18" />
        </div>
        <div class="health-item__content">
          <span class="health-item__label">Docker</span>
          <span class="health-item__value">{{ dockerRunning }}/{{ dockerTotal }}</span>
        </div>
        <div class="health-item__sub">running</div>
      </div>

      <!-- DB -->
      <div class="health-item" @click="navigateTo('db')">
        <div class="health-item__icon" :style="{ backgroundColor: getColorBg('db'), color: getColor('db') }">
          <LIcon icon="mdi-database" size="18" />
        </div>
        <div class="health-item__content">
          <span class="health-item__label">DB</span>
          <span class="health-item__value">{{ dbStatus }}</span>
        </div>
      </div>

      <!-- Details Link -->
      <div class="health-item health-item--link" @click="navigateTo('health')">
        <LIcon icon="mdi-arrow-right" size="18" />
        <span>Details</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { io } from 'socket.io-client'
import { useAuth } from '@/composables/useAuth'

const emit = defineEmits(['navigate'])

const SOCKET_URL = import.meta.env.VITE_API_BASE_URL || window.location.origin

// State
const loading = ref(true)
const connected = ref(false)
const hostData = ref(null)
const apiData = ref(null)
const wsData = ref(null)
const dockerData = ref(null)

let socket = null

// Computed values
const cpuPercent = computed(() => Math.round(hostData.value?.cpu?.percent ?? 0))
const memoryPercent = computed(() => Math.round(hostData.value?.memory?.ram?.percent ?? 0))

const requestsPerSec = computed(() => apiData.value?.stats?.requests_per_sec?.toFixed(1) ?? '0')
const avgLatency = computed(() => Math.round(apiData.value?.stats?.avg_latency_ms ?? 0))
const errorRate = computed(() => apiData.value?.stats?.error_rate ?? 0)

const wsConnections = computed(() => wsData.value?.total_connections ?? 0)

const dockerTotal = computed(() => dockerData.value?.summary?.total ?? 0)
const dockerRunning = computed(() => dockerData.value?.summary?.running ?? 0)

const dbStatus = computed(() => connected.value ? 'OK' : '-')

// Color logic
function getColor(type) {
  const colors = {
    host: getHealthColor(cpuPercent.value),
    api: errorRate.value > 2 ? '#e8a087' : (errorRate.value > 0.5 ? '#e8c87a' : '#98d4bb'),
    ws: '#88c4c8',
    docker: dockerRunning.value === dockerTotal.value ? '#98d4bb' : '#e8c87a',
    db: connected.value ? '#98d4bb' : '#9e9e9e',
  }
  return colors[type] || '#9e9e9e'
}

function getColorBg(type) {
  const color = getColor(type)
  return hexToRgba(color, 0.15)
}

function getHealthColor(percent) {
  if (percent < 60) return '#98d4bb'
  if (percent < 80) return '#e8c87a'
  return '#e8a087'
}

function hexToRgba(hex, alpha) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  if (!result) return `rgba(0, 0, 0, ${alpha})`
  const r = parseInt(result[1], 16)
  const g = parseInt(result[2], 16)
  const b = parseInt(result[3], 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

function navigateTo(section) {
  emit('navigate', section)
}

// Socket connection
function connect() {
  const auth = useAuth()
  const token = auth.getToken()

  socket = io(`${SOCKET_URL}/admin`, {
    transports: ['polling', 'websocket'],
    query: { token },
    reconnection: true,
    reconnectionAttempts: 3,
    reconnectionDelay: 2000,
  })

  socket.on('connect', () => {
    connected.value = true
    loading.value = false

    // Subscribe to all metrics
    socket.emit('host:subscribe', {})
    socket.emit('api:subscribe', { window: '5min' })
    socket.emit('ws:subscribe', {})
    socket.emit('docker:subscribe_stats', { scope: 'project' })
  })

  socket.on('disconnect', () => {
    connected.value = false
  })

  socket.on('host:stats', (data) => {
    hostData.value = data
    loading.value = false
  })

  socket.on('api:stats', (data) => {
    apiData.value = data
  })

  socket.on('ws:stats', (data) => {
    wsData.value = data
  })

  socket.on('docker:stats', (data) => {
    dockerData.value = data
  })
}

function disconnect() {
  if (socket) {
    socket.emit('host:unsubscribe', {})
    socket.emit('api:unsubscribe', {})
    socket.emit('ws:unsubscribe', {})
    socket.emit('docker:unsubscribe_stats', { scope: 'project' })
    socket.disconnect()
    socket = null
  }
}

onMounted(() => {
  connect()
})

onBeforeUnmount(() => {
  disconnect()
})
</script>

<style scoped>
.health-bar {
  background: rgb(var(--v-theme-surface));
  border-radius: 12px 4px 12px 4px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  padding: 12px 16px;
  transition: opacity 0.3s ease;
}

.health-bar--loading {
  opacity: 0.6;
}

.health-bar__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.health-bar__title {
  display: flex;
  align-items: center;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.health-bar__live {
  animation: pulse-live 2s ease-in-out infinite;
}

@keyframes pulse-live {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.health-bar__items {
  display: flex;
  align-items: center;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.health-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px 2px 8px 2px;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.health-item:hover {
  background: rgba(var(--v-theme-on-surface), 0.06);
  transform: translateY(-1px);
}

.health-item--link {
  background: transparent;
  color: var(--llars-primary, #b0ca97);
  font-weight: 500;
  font-size: 0.8rem;
}

.health-item--link:hover {
  background: rgba(var(--v-theme-primary), 0.08);
}

.health-item__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 6px 2px 6px 2px;
  flex-shrink: 0;
}

.health-item__content {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.health-item__label {
  font-size: 0.65rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.health-item__value {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.health-item__sub {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.health-item__indicator {
  display: flex;
  gap: 3px;
}

.health-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.15);
  transition: background-color 0.3s ease;
}

.health-dot.active {
  background: var(--llars-primary, #b0ca97);
}

@media (max-width: 768px) {
  .health-bar__items {
    gap: 8px;
  }

  .health-item {
    padding: 6px 10px;
  }

  .health-item__icon {
    width: 28px;
    height: 28px;
  }
}
</style>
