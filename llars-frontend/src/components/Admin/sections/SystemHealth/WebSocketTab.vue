<template>
  <div class="websocket-tab">
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
        icon="mdi-connection"
        label="Active"
        :value="totalConnections"
        :percent="0"
        :show-progress="false"
        subtitle="Connections"
        color="primary"
        color-mode="fixed"
        :loading="loading"
      />
      <LGauge
        icon="mdi-arrow-down"
        label="Messages In"
        :value="messagesInPerSec"
        suffix="/s"
        :percent="0"
        :show-progress="false"
        :subtitle="`${formatBytes(bytesInPerSec)}/s`"
        color="success"
        color-mode="fixed"
        :loading="loading"
      />
      <LGauge
        icon="mdi-arrow-up"
        label="Messages Out"
        :value="messagesOutPerSec"
        suffix="/s"
        :percent="0"
        :show-progress="false"
        :subtitle="`${formatBytes(bytesOutPerSec)}/s`"
        color="accent"
        color-mode="fixed"
        :loading="loading"
      />
      <LGauge
        icon="mdi-swap-vertical"
        label="Bandwidth"
        :value="formatBytes(totalBandwidth)"
        suffix="/s"
        :percent="0"
        :show-progress="false"
        :subtitle="`↓${formatBytes(bytesInPerSec)} ↑${formatBytes(bytesOutPerSec)}`"
        color="secondary"
        color-mode="fixed"
        :loading="loading"
      />
    </div>

    <!-- Charts Row -->
    <div class="charts-row">
      <div class="chart-card">
        <LChart
          title="Connections (5min)"
          :data="connectionHistory"
          :max-points="60"
          color="primary"
          :height="120"
          :min-y="0"
        />
      </div>
      <div class="chart-card">
        <LChart
          title="Message Rate (5min)"
          :series="[
            { data: messageInHistory, color: 'success', label: 'In' },
            { data: messageOutHistory, color: 'accent', label: 'Out' }
          ]"
          :max-points="60"
          :height="120"
          :min-y="0"
        />
      </div>
    </div>

    <!-- Namespace Breakdown -->
    <div class="section-card">
      <h3 class="section-card__title">
        <LIcon icon="mdi-format-list-group" size="18" class="mr-2" />
        Namespace Breakdown
      </h3>
      <div class="namespace-table">
        <div class="namespace-header">
          <span class="ns-col ns-col--name">Namespace</span>
          <span class="ns-col ns-col--clients">Clients</span>
          <span class="ns-col ns-col--rooms">Rooms</span>
          <span class="ns-col ns-col--in">Msg/s In</span>
          <span class="ns-col ns-col--out">Msg/s Out</span>
        </div>
        <div
          v-for="ns in namespaces"
          :key="ns.namespace"
          class="namespace-row"
        >
          <span class="ns-col ns-col--name">
            <LIcon :icon="getNamespaceIcon(ns.namespace)" size="16" class="mr-2" />
            {{ ns.label }}
          </span>
          <span class="ns-col ns-col--clients">
            <LTag variant="primary" size="sm">{{ ns.clients }}</LTag>
          </span>
          <span class="ns-col ns-col--rooms">{{ ns.rooms }}</span>
          <span class="ns-col ns-col--in">{{ ns.messages_in_per_sec }}</span>
          <span class="ns-col ns-col--out">{{ ns.messages_out_per_sec }}</span>
        </div>
        <div v-if="!namespaces.length && !loading" class="namespace-empty">
          Keine aktiven Namespaces
        </div>
      </div>
    </div>

    <!-- Recent Events -->
    <div class="section-card">
      <h3 class="section-card__title">
        <LIcon icon="mdi-history" size="18" class="mr-2" />
        Connection Events
      </h3>
      <div class="events-list">
        <div
          v-for="(event, idx) in recentEvents"
          :key="idx"
          class="event-item"
          :class="{ 'event-item--connect': event.event_type === 'connect' }"
        >
          <LIcon
            :icon="event.event_type === 'connect' ? 'mdi-login' : 'mdi-logout'"
            :color="event.event_type === 'connect' ? 'success' : 'grey'"
            size="16"
          />
          <span class="event-item__user">
            {{ event.username || event.sid }}
          </span>
          <LTag variant="gray" size="sm">
            {{ event.namespace_label }}
          </LTag>
          <span v-if="event.reason" class="event-item__reason">
            ({{ event.reason }})
          </span>
          <span class="event-item__age">{{ formatAge(event.age_seconds) }}</span>
        </div>
        <div v-if="!recentEvents.length && !loading" class="events-empty">
          Keine Verbindungs-Events
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, inject } from 'vue'
import { useWebSocketMetrics } from './composables/useSystemHealth'

const {
  connected,
  loading,
  error,
  data,
  connectionHistory,
  messageInHistory,
  messageOutHistory,
  connect,
  disconnect,
} = useWebSocketMetrics()

// Provide connection status to parent
const setWsConnected = inject('setWsConnected', () => {})

watch(connected, (val) => {
  setWsConnected(val)
})

// Computed values from data
const totalConnections = computed(() => data.value?.total_connections ?? 0)

const rates = computed(() => data.value?.rates ?? {})
const messagesInPerSec = computed(() => rates.value.messages_in_per_sec ?? 0)
const messagesOutPerSec = computed(() => rates.value.messages_out_per_sec ?? 0)
const bytesInPerSec = computed(() => rates.value.bytes_in_per_sec ?? 0)
const bytesOutPerSec = computed(() => rates.value.bytes_out_per_sec ?? 0)
const totalBandwidth = computed(() => bytesInPerSec.value + bytesOutPerSec.value)

const namespaces = computed(() => data.value?.namespaces ?? [])
const recentEvents = computed(() => data.value?.recent_events ?? [])

const namespaceIcons = {
  '/': 'mdi-home',
  '/admin': 'mdi-shield-account',
  '/chat': 'mdi-chat',
  '/collab': 'mdi-account-group',
  '/judge': 'mdi-gavel',
  '/crawler': 'mdi-spider-web',
  '/oncoco': 'mdi-file-document',
}

function getNamespaceIcon(ns) {
  return namespaceIcons[ns] || 'mdi-connection'
}

function formatBytes(bytes) {
  if (bytes === undefined || bytes === null) return '0 B'
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(Math.abs(bytes)) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function formatAge(seconds) {
  if (seconds < 60) return `${Math.round(seconds)}s ago`
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`
  return `${Math.round(seconds / 3600)}h ago`
}

onMounted(() => {
  connect()
})

onBeforeUnmount(() => {
  disconnect()
})
</script>

<style scoped>
.websocket-tab {
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

/* Namespace Table */
.namespace-table {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-x: auto;
}

.namespace-header,
.namespace-row {
  display: grid;
  grid-template-columns: 1fr 80px 80px 80px 80px;
  gap: 12px;
  align-items: center;
  padding: 8px 0;
}

.namespace-header {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.namespace-row {
  font-size: 0.85rem;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.04);
}

.namespace-row:hover {
  background: rgba(var(--v-theme-on-surface), 0.02);
}

.ns-col--name {
  display: flex;
  align-items: center;
}

.ns-col--clients,
.ns-col--rooms,
.ns-col--in,
.ns-col--out {
  text-align: center;
}

.namespace-empty {
  text-align: center;
  padding: 20px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 0.875rem;
}

/* Events List */
.events-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.event-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 6px 2px 6px 2px;
  font-size: 0.8rem;
}

.event-item--connect {
  background: rgba(var(--v-theme-success), 0.05);
}

.event-item__user {
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
}

.event-item__reason {
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 0.75rem;
}

.event-item__age {
  margin-left: auto;
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 0.7rem;
  flex-shrink: 0;
}

.events-empty {
  text-align: center;
  padding: 20px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 0.875rem;
}

@media (max-width: 600px) {
  .gauges-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-row {
    grid-template-columns: 1fr;
  }

  .namespace-header,
  .namespace-row {
    grid-template-columns: 1fr 60px 60px;
  }

  .ns-col--rooms,
  .ns-col--out {
    display: none;
  }
}
</style>
