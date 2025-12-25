<template>
  <div class="system-health-section">
    <!-- Header -->
    <div class="section-header">
      <div class="section-header__left">
        <h2 class="section-title">System Health</h2>
        <LTag
          :variant="overallHealth.variant"
          size="sm"
          :prepend-icon="overallHealth.icon"
        >
          {{ overallHealth.label }}
        </LTag>
      </div>
      <div class="section-header__right">
        <LTag
          v-if="isConnected"
          variant="success"
          size="sm"
          prepend-icon="mdi-circle-small"
          class="live-indicator"
        >
          Live
        </LTag>
        <LTag v-else variant="gray" size="sm" prepend-icon="mdi-circle-small">
          Offline
        </LTag>
      </div>
    </div>

    <!-- Sub-Tabs -->
    <LTabs
      v-model="activeTab"
      :tabs="tabs"
      class="sub-tabs"
    />

    <!-- Tab Content -->
    <div class="tab-content">
      <HostMetricsTab v-if="activeTab === 'host'" />
      <ApiPerformanceTab v-else-if="activeTab === 'api'" />
      <WebSocketTab v-else-if="activeTab === 'websocket'" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, provide } from 'vue'
import HostMetricsTab from './SystemHealth/HostMetricsTab.vue'
import ApiPerformanceTab from './SystemHealth/ApiPerformanceTab.vue'
import WebSocketTab from './SystemHealth/WebSocketTab.vue'

const activeTab = ref('host')

const tabs = [
  { value: 'host', label: 'Host', icon: 'mdi-server' },
  { value: 'api', label: 'API Performance', icon: 'mdi-api' },
  { value: 'websocket', label: 'WebSocket', icon: 'mdi-connection' },
]

// Track connection status from child components
const hostConnected = ref(false)
const apiConnected = ref(false)
const wsConnected = ref(false)

// Provide setters for child components
provide('setHostConnected', (v) => { hostConnected.value = v })
provide('setApiConnected', (v) => { apiConnected.value = v })
provide('setWsConnected', (v) => { wsConnected.value = v })

const isConnected = computed(() => {
  switch (activeTab.value) {
    case 'host': return hostConnected.value
    case 'api': return apiConnected.value
    case 'websocket': return wsConnected.value
    default: return false
  }
})

// Track health metrics from child components
const hostHealth = ref({ status: 'unknown', cpu: 0, memory: 0 })
const apiHealth = ref({ status: 'unknown', errorRate: 0 })

provide('setHostHealth', (v) => { hostHealth.value = v })
provide('setApiHealth', (v) => { apiHealth.value = v })

const overallHealth = computed(() => {
  // Determine overall health based on metrics
  const cpu = hostHealth.value.cpu || 0
  const memory = hostHealth.value.memory || 0
  const errorRate = apiHealth.value.errorRate || 0

  // Critical conditions
  if (cpu > 90 || memory > 95 || errorRate > 5) {
    return { variant: 'danger', icon: 'mdi-alert-circle', label: 'Critical' }
  }

  // Warning conditions
  if (cpu > 75 || memory > 85 || errorRate > 2) {
    return { variant: 'warning', icon: 'mdi-alert', label: 'Warning' }
  }

  // All good
  if (hostConnected.value || apiConnected.value) {
    return { variant: 'success', icon: 'mdi-check-circle', label: 'Healthy' }
  }

  return { variant: 'gray', icon: 'mdi-help-circle', label: 'Unknown' }
})
</script>

<style scoped>
.system-health-section {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
}

.section-header__left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-header__right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.live-indicator {
  animation: pulse-live 2s ease-in-out infinite;
}

@keyframes pulse-live {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.sub-tabs {
  padding: 0 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
</style>
