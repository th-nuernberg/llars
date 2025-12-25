<template>
  <div class="api-metrics-tab">
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
        icon="mdi-lightning-bolt"
        label="Requests/s"
        :value="requestsPerSec"
        :percent="0"
        :show-progress="false"
        :subtitle="`${requestCount} requests (5min)`"
        color="primary"
        color-mode="fixed"
        :loading="loading"
      />
      <LGauge
        icon="mdi-timer-outline"
        label="Avg Latency"
        :value="avgLatency"
        suffix="ms"
        :percent="latencyPercent"
        :subtitle="`P95: ${p95Latency}ms`"
        color-mode="threshold"
        :loading="loading"
      />
      <LGauge
        icon="mdi-check-circle"
        label="Success Rate"
        :value="successRate"
        suffix="%"
        :percent="successRate"
        color-mode="inverse"
        :loading="loading"
      />
      <LGauge
        icon="mdi-alert-circle"
        label="Errors"
        :value="errorCount"
        :percent="0"
        :show-progress="false"
        :subtitle="`${errorRate}% error rate`"
        :color="errorCount > 0 ? 'danger' : 'success'"
        color-mode="fixed"
        :loading="loading"
      />
    </div>

    <!-- Charts Row -->
    <div class="charts-row">
      <div class="chart-card">
        <LChart
          title="Request Rate (5min)"
          :data="requestRateHistory"
          :max-points="60"
          color="primary"
          :height="120"
          :min-y="0"
        />
      </div>
      <div class="chart-card">
        <LChart
          title="Latency (5min)"
          :data="latencyHistory"
          :max-points="60"
          color="accent"
          :height="120"
          :min-y="0"
        />
      </div>
    </div>

    <!-- Latency Distribution -->
    <div class="section-card">
      <h3 class="section-card__title">
        <v-icon icon="mdi-chart-bar" size="18" class="mr-2" />
        Latency Distribution
      </h3>
      <div class="latency-bars">
        <div class="latency-bar">
          <span class="latency-bar__label">P50</span>
          <div class="latency-bar__track">
            <div
              class="latency-bar__fill latency-bar__fill--p50"
              :style="{ width: `${p50Width}%` }"
            />
          </div>
          <span class="latency-bar__value">{{ p50Latency }}ms</span>
        </div>
        <div class="latency-bar">
          <span class="latency-bar__label">P95</span>
          <div class="latency-bar__track">
            <div
              class="latency-bar__fill latency-bar__fill--p95"
              :style="{ width: `${p95Width}%` }"
            />
          </div>
          <span class="latency-bar__value">{{ p95Latency }}ms</span>
        </div>
        <div class="latency-bar">
          <span class="latency-bar__label">P99</span>
          <div class="latency-bar__track">
            <div
              class="latency-bar__fill latency-bar__fill--p99"
              :style="{ width: `${p99Width}%` }"
            />
          </div>
          <span class="latency-bar__value">{{ p99Latency }}ms</span>
        </div>
      </div>
    </div>

    <!-- Top Endpoints -->
    <div class="section-card">
      <h3 class="section-card__title">
        <v-icon icon="mdi-api" size="18" class="mr-2" />
        Top Endpoints (by latency)
      </h3>
      <div class="endpoints-table">
        <div class="endpoints-header">
          <span class="endpoint-col endpoint-col--method">Method</span>
          <span class="endpoint-col endpoint-col--path">Path</span>
          <span class="endpoint-col endpoint-col--count">Calls</span>
          <span class="endpoint-col endpoint-col--avg">Avg</span>
          <span class="endpoint-col endpoint-col--p95">P95</span>
          <span class="endpoint-col endpoint-col--errors">Errors</span>
        </div>
        <div
          v-for="(ep, idx) in topEndpoints"
          :key="idx"
          class="endpoint-row"
        >
          <span class="endpoint-col endpoint-col--method">
            <LTag :variant="getMethodVariant(ep.method)" size="sm">
              {{ ep.method }}
            </LTag>
          </span>
          <span class="endpoint-col endpoint-col--path" :title="ep.path">
            {{ ep.path }}
          </span>
          <span class="endpoint-col endpoint-col--count">{{ ep.count }}</span>
          <span class="endpoint-col endpoint-col--avg">{{ ep.avg_latency_ms }}ms</span>
          <span class="endpoint-col endpoint-col--p95">{{ ep.p95_latency_ms }}ms</span>
          <span class="endpoint-col endpoint-col--errors">
            <LTag
              v-if="ep.error_count > 0"
              variant="danger"
              size="sm"
            >
              {{ ep.error_count }} ({{ ep.error_rate }}%)
            </LTag>
            <span v-else class="text-success">-</span>
          </span>
        </div>
        <div v-if="!topEndpoints.length && !loading" class="endpoints-empty">
          Keine Endpoint-Daten verfügbar
        </div>
      </div>
    </div>

    <!-- Recent Errors -->
    <div v-if="recentErrors.length > 0" class="section-card section-card--errors">
      <h3 class="section-card__title">
        <v-icon icon="mdi-alert" size="18" class="mr-2" color="error" />
        Recent Errors
      </h3>
      <div class="errors-list">
        <div
          v-for="(err, idx) in recentErrors"
          :key="idx"
          class="error-item"
        >
          <LTag :variant="getStatusVariant(err.status_code)" size="sm">
            {{ err.status_code }}
          </LTag>
          <span class="error-item__method">{{ err.method }}</span>
          <span class="error-item__path">{{ err.path }}</span>
          <span class="error-item__message" :title="err.error">
            {{ err.error || 'No message' }}
          </span>
          <span class="error-item__age">{{ formatAge(err.age_seconds) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, inject } from 'vue'
import { useApiMetrics } from './composables/useSystemHealth'

const {
  connected,
  loading,
  error,
  data,
  requestRateHistory,
  latencyHistory,
  errorRateHistory,
  connect,
  disconnect,
} = useApiMetrics()

// Provide connection status to parent
const setApiConnected = inject('setApiConnected', () => {})
const setApiHealth = inject('setApiHealth', () => {})

watch(connected, (val) => {
  setApiConnected(val)
})

// Computed values from data
const stats = computed(() => data.value?.stats ?? {})

const requestsPerSec = computed(() => stats.value.requests_per_sec ?? 0)
const requestCount = computed(() => stats.value.request_count ?? 0)

const avgLatency = computed(() => Math.round(stats.value.avg_latency_ms ?? 0))
const p50Latency = computed(() => Math.round(stats.value.p50_latency_ms ?? 0))
const p95Latency = computed(() => Math.round(stats.value.p95_latency_ms ?? 0))
const p99Latency = computed(() => Math.round(stats.value.p99_latency_ms ?? 0))

// Calculate latency bar widths (relative to max)
const maxLatency = computed(() => Math.max(p99Latency.value, 1))
const p50Width = computed(() => (p50Latency.value / maxLatency.value) * 100)
const p95Width = computed(() => (p95Latency.value / maxLatency.value) * 100)
const p99Width = computed(() => 100) // Always full width for P99

// Latency percent for gauge (threshold at 500ms = 100%)
const latencyPercent = computed(() => Math.min(100, (avgLatency.value / 500) * 100))

const errorCount = computed(() => stats.value.error_count ?? 0)
const errorRate = computed(() => stats.value.error_rate ?? 0)
const successRate = computed(() => 100 - errorRate.value)

const topEndpoints = computed(() => (stats.value.endpoints ?? []).slice(0, 10))
const recentErrors = computed(() => data.value?.recent_errors ?? [])

// Update parent health status
watch([errorRate], () => {
  setApiHealth({
    status: 'connected',
    errorRate: errorRate.value,
  })
})

function getMethodVariant(method) {
  const variants = {
    GET: 'info',
    POST: 'success',
    PUT: 'warning',
    PATCH: 'warning',
    DELETE: 'danger',
  }
  return variants[method] || 'gray'
}

function getStatusVariant(code) {
  if (code >= 500) return 'danger'
  if (code >= 400) return 'warning'
  return 'gray'
}

function formatAge(seconds) {
  if (seconds < 60) return `${Math.round(seconds)}s ago`
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`
  return `${Math.round(seconds / 3600)}h ago`
}

onMounted(() => {
  connect('5min')
})

onBeforeUnmount(() => {
  disconnect()
})
</script>

<style scoped>
.api-metrics-tab {
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

.section-card--errors {
  border-color: rgba(var(--v-theme-error), 0.2);
}

.section-card__title {
  display: flex;
  align-items: center;
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

/* Latency Bars */
.latency-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.latency-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.latency-bar__label {
  width: 40px;
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.latency-bar__track {
  flex: 1;
  height: 12px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 6px;
  overflow: hidden;
}

.latency-bar__fill {
  height: 100%;
  border-radius: 6px;
  transition: width 0.5s ease;
}

.latency-bar__fill--p50 {
  background: var(--llars-success, #98d4bb);
}

.latency-bar__fill--p95 {
  background: var(--llars-warning, #e8c87a);
}

.latency-bar__fill--p99 {
  background: var(--llars-danger, #e8a087);
}

.latency-bar__value {
  width: 70px;
  text-align: right;
  font-size: 0.8rem;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
}

/* Endpoints Table */
.endpoints-table {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-x: auto;
}

.endpoints-header,
.endpoint-row {
  display: grid;
  grid-template-columns: 80px 1fr 70px 70px 70px 100px;
  gap: 12px;
  align-items: center;
  padding: 8px 0;
}

.endpoints-header {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.endpoint-row {
  font-size: 0.8rem;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.04);
}

.endpoint-row:hover {
  background: rgba(var(--v-theme-on-surface), 0.02);
}

.endpoint-col--path {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: monospace;
  font-size: 0.75rem;
}

.endpoint-col--count,
.endpoint-col--avg,
.endpoint-col--p95 {
  text-align: right;
}

.endpoints-empty {
  text-align: center;
  padding: 20px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 0.875rem;
}

/* Errors List */
.errors-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.error-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  background: rgba(var(--v-theme-error), 0.05);
  border-radius: 6px 2px 6px 2px;
  font-size: 0.8rem;
}

.error-item__method {
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.error-item__path {
  font-family: monospace;
  font-size: 0.75rem;
  color: rgb(var(--v-theme-on-surface));
  flex-shrink: 0;
}

.error-item__message {
  flex: 1;
  color: rgba(var(--v-theme-on-surface), 0.6);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.error-item__age {
  flex-shrink: 0;
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 0.7rem;
}

.text-success {
  color: var(--llars-success, #98d4bb);
}

@media (max-width: 600px) {
  .gauges-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-row {
    grid-template-columns: 1fr;
  }

  .endpoints-header,
  .endpoint-row {
    grid-template-columns: 60px 1fr 50px 60px;
  }

  .endpoint-col--p95,
  .endpoint-col--errors {
    display: none;
  }
}
</style>
