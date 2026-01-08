<template>
  <div class="host-metrics-tab">
    <!-- Error Alert -->
    <v-alert
      v-if="error"
      type="error"
      variant="tonal"
      density="compact"
      class="mb-4"
      closable
      @click:close="error = null"
    >
      {{ error }}
    </v-alert>

    <!-- Gauges Row -->
    <div class="gauges-row">
      <LGauge
        icon="mdi-chip"
        label="CPU"
        :value="cpuPercent"
        suffix="%"
        :percent="cpuPercent"
        :subtitle="cpuSubtitle"
        color-mode="threshold"
        :loading="loading"
      />
      <LGauge
        icon="mdi-memory"
        label="RAM"
        :value="memoryPercent"
        suffix="%"
        :percent="memoryPercent"
        :subtitle="memorySubtitle"
        color-mode="threshold"
        :loading="loading"
      />
      <LGauge
        icon="mdi-swap-vertical"
        label="Swap"
        :value="swapPercent"
        suffix="%"
        :percent="swapPercent"
        :subtitle="swapSubtitle"
        color-mode="threshold"
        :loading="loading"
      />
      <LGauge
        icon="mdi-ethernet"
        label="Network"
        :value="formatBytes(networkRate)"
        suffix="/s"
        :percent="0"
        :show-progress="false"
        :subtitle="networkSubtitle"
        color="accent"
        color-mode="fixed"
        :loading="loading"
      />
    </div>

    <!-- Charts Row -->
    <div class="charts-row">
      <div class="chart-card">
        <LChart
          title="CPU Usage (60s)"
          :data="cpuHistory"
          :max-points="60"
          color="primary"
          :height="120"
          :min-y="0"
          :max-y="100"
        />
      </div>
      <div class="chart-card">
        <LChart
          title="Memory Usage (60s)"
          :data="memoryHistory"
          :max-points="60"
          color="accent"
          :height="120"
          :min-y="0"
          :max-y="100"
        />
      </div>
    </div>

    <!-- Disk Usage -->
    <div class="section-card">
      <h3 class="section-card__title">
        <LIcon icon="mdi-harddisk" size="18" class="mr-2" />
        Disk Usage
      </h3>
      <div class="disk-list">
        <div
          v-for="disk in diskPartitions"
          :key="disk.mountpoint"
          class="disk-item"
        >
          <div class="disk-item__header">
            <span class="disk-item__mount">{{ disk.mountpoint }}</span>
            <span class="disk-item__size">
              {{ formatBytes(disk.used) }} / {{ formatBytes(disk.total) }}
            </span>
          </div>
          <div class="disk-item__bar">
            <div
              class="disk-item__fill"
              :style="{ width: `${disk.percent}%` }"
              :class="getDiskClass(disk.percent)"
            />
          </div>
          <div class="disk-item__footer">
            <span class="disk-item__device">{{ disk.device }}</span>
            <span class="disk-item__percent">{{ disk.percent }}%</span>
          </div>
        </div>
        <div v-if="!diskPartitions.length && !loading" class="disk-empty">
          Keine Disk-Informationen verfügbar
        </div>
      </div>
    </div>

    <!-- System Info -->
    <div class="section-card">
      <h3 class="section-card__title">
        <LIcon icon="mdi-information" size="18" class="mr-2" />
        System Info
      </h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-item__label">Uptime</span>
          <span class="info-item__value">{{ uptime }}</span>
        </div>
        <div class="info-item">
          <span class="info-item__label">Load Average</span>
          <span class="info-item__value">{{ loadAverage }}</span>
        </div>
        <div class="info-item">
          <span class="info-item__label">CPU Cores</span>
          <span class="info-item__value">{{ cpuCores }}</span>
        </div>
        <div class="info-item">
          <span class="info-item__label">Platform</span>
          <span class="info-item__value">{{ platform }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, inject } from 'vue'
import { useHostMetrics } from './composables/useSystemHealth'

const {
  connected,
  loading,
  error,
  data,
  cpuHistory,
  memoryHistory,
  networkHistory,
  connect,
  disconnect,
} = useHostMetrics()

// Provide connection status to parent
const setHostConnected = inject('setHostConnected', () => {})
const setHostHealth = inject('setHostHealth', () => {})

watch(connected, (val) => {
  setHostConnected(val)
})

// Computed values from data
const cpuPercent = computed(() => data.value?.cpu?.percent ?? 0)
const cpuSubtitle = computed(() => {
  const load = data.value?.cpu?.load_avg
  if (!load) return ''
  return `Load: ${load['1min']} / ${load['5min']} / ${load['15min']}`
})

const memoryPercent = computed(() => data.value?.memory?.ram?.percent ?? 0)
const memorySubtitle = computed(() => {
  const ram = data.value?.memory?.ram
  if (!ram) return ''
  return `${formatBytes(ram.used)} / ${formatBytes(ram.total)}`
})

const swapPercent = computed(() => data.value?.memory?.swap?.percent ?? 0)
const swapSubtitle = computed(() => {
  const swap = data.value?.memory?.swap
  if (!swap) return ''
  return `${formatBytes(swap.used)} / ${formatBytes(swap.total)}`
})

const networkRate = computed(() => {
  const rates = data.value?.network?.rates
  if (!rates) return 0
  return (rates.bytes_recv_sec ?? 0) + (rates.bytes_sent_sec ?? 0)
})
const networkSubtitle = computed(() => {
  const rates = data.value?.network?.rates
  if (!rates) return ''
  return `↓${formatBytes(rates.bytes_recv_sec)}/s ↑${formatBytes(rates.bytes_sent_sec)}/s`
})

const diskPartitions = computed(() => data.value?.disk?.partitions ?? [])

const uptime = computed(() => data.value?.system?.uptime_formatted ?? '-')
const loadAverage = computed(() => {
  const load = data.value?.cpu?.load_avg
  if (!load) return '-'
  return `${load['1min']} / ${load['5min']} / ${load['15min']}`
})
const cpuCores = computed(() => {
  const cpu = data.value?.cpu
  if (!cpu) return '-'
  return `${cpu.count_physical} physical / ${cpu.count_logical} logical`
})
const platform = computed(() => {
  const sys = data.value?.system?.platform
  if (!sys) return '-'
  return `${sys.system} ${sys.release} (${sys.machine})`
})

// Update parent health status
watch([cpuPercent, memoryPercent], () => {
  setHostHealth({
    status: 'connected',
    cpu: cpuPercent.value,
    memory: memoryPercent.value,
  })
})

function formatBytes(bytes) {
  if (bytes === undefined || bytes === null) return '0 B'
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(Math.abs(bytes)) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function getDiskClass(percent) {
  if (percent >= 90) return 'disk-item__fill--danger'
  if (percent >= 75) return 'disk-item__fill--warning'
  return 'disk-item__fill--success'
}

onMounted(() => {
  connect()
})

onBeforeUnmount(() => {
  disconnect()
})
</script>

<style scoped>
.host-metrics-tab {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.gauges-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.charts-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.chart-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 12px 4px 12px 4px;
  padding: 16px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.section-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 12px 4px 12px 4px;
  padding: 16px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.section-card__title {
  display: flex;
  align-items: center;
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.disk-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.disk-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.disk-item__header {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
}

.disk-item__mount {
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
}

.disk-item__size {
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.disk-item__bar {
  height: 8px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 4px;
  overflow: hidden;
}

.disk-item__fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.disk-item__fill--success {
  background: var(--llars-success, #98d4bb);
}

.disk-item__fill--warning {
  background: var(--llars-warning, #e8c87a);
}

.disk-item__fill--danger {
  background: var(--llars-danger, #e8a087);
}

.disk-item__footer {
  display: flex;
  justify-content: space-between;
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.disk-empty {
  text-align: center;
  padding: 20px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 0.875rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.info-item__label {
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.info-item__value {
  font-size: 0.875rem;
  color: rgb(var(--v-theme-on-surface));
}

@media (max-width: 600px) {
  .gauges-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-row {
    grid-template-columns: 1fr;
  }
}
</style>
