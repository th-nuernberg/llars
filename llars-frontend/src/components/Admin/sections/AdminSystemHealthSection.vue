<template>
  <div class="system-health-section">
    <!-- Header -->
    <div class="health-header">
      <div class="header-title">
        <div class="title-icon" :class="healthIconClass">
          <LIcon size="20" color="white">{{ overallHealth.icon }}</LIcon>
        </div>
        <div>
          <h2 class="text-subtitle-1 font-weight-bold">System Health</h2>
          <div class="header-status">
            <span class="status-text" :class="statusTextClass">{{ overallHealth.label }}</span>
            <span class="status-separator">|</span>
            <span class="connection-status" :class="{ 'connection-status--live': isConnected }">
              <span class="connection-dot" />
              {{ isConnected ? 'Live' : 'Offline' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Quick Stats -->
      <div class="header-stats">
        <div class="quick-stat" :class="getCpuClass">
          <LIcon size="14">mdi-chip</LIcon>
          <span class="quick-stat__value">{{ hostHealth.cpu?.toFixed(0) || 0 }}%</span>
          <span class="quick-stat__label">CPU</span>
        </div>
        <div class="quick-stat" :class="getMemoryClass">
          <LIcon size="14">mdi-memory</LIcon>
          <span class="quick-stat__value">{{ hostHealth.memory?.toFixed(0) || 0 }}%</span>
          <span class="quick-stat__label">RAM</span>
        </div>
        <div class="quick-stat" :class="getApiClass">
          <LIcon size="14">mdi-api</LIcon>
          <span class="quick-stat__value">{{ apiHealth.errorRate?.toFixed(1) || 0 }}%</span>
          <span class="quick-stat__label">Errors</span>
        </div>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="tab-nav">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === tab.value }"
        @click="activeTab = tab.value"
      >
        <LIcon size="16" class="tab-btn__icon">{{ tab.icon }}</LIcon>
        <span class="tab-btn__label">{{ tab.label }}</span>
        <span v-if="tab.value === 'host' && hostConnected" class="tab-btn__indicator tab-btn__indicator--success" />
        <span v-else-if="tab.value === 'api' && apiConnected" class="tab-btn__indicator tab-btn__indicator--success" />
        <span v-else-if="tab.value === 'websocket' && wsConnected" class="tab-btn__indicator tab-btn__indicator--success" />
      </button>
    </div>

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
  { value: 'host', label: 'Host Metrics', icon: 'mdi-server' },
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
  const cpu = hostHealth.value.cpu || 0
  const memory = hostHealth.value.memory || 0
  const errorRate = apiHealth.value.errorRate || 0

  // Critical conditions
  if (cpu > 90 || memory > 95 || errorRate > 5) {
    return { variant: 'danger', icon: 'mdi-alert-circle', label: 'Critical', color: '#f44336' }
  }

  // Warning conditions
  if (cpu > 75 || memory > 85 || errorRate > 2) {
    return { variant: 'warning', icon: 'mdi-alert', label: 'Warning', color: '#FF9800' }
  }

  // All good
  if (hostConnected.value || apiConnected.value) {
    return { variant: 'success', icon: 'mdi-check-circle', label: 'Healthy', color: '#4CAF50' }
  }

  return { variant: 'gray', icon: 'mdi-help-circle', label: 'Unknown', color: '#9E9E9E' }
})

const healthIconClass = computed(() => ({
  'title-icon--success': overallHealth.value.variant === 'success',
  'title-icon--warning': overallHealth.value.variant === 'warning',
  'title-icon--danger': overallHealth.value.variant === 'danger',
  'title-icon--gray': overallHealth.value.variant === 'gray',
}))

const statusTextClass = computed(() => ({
  'text-success': overallHealth.value.variant === 'success',
  'text-warning': overallHealth.value.variant === 'warning',
  'text-error': overallHealth.value.variant === 'danger',
}))

const getCpuClass = computed(() => {
  const cpu = hostHealth.value.cpu || 0
  if (cpu > 90) return 'quick-stat--danger'
  if (cpu > 75) return 'quick-stat--warning'
  return 'quick-stat--success'
})

const getMemoryClass = computed(() => {
  const memory = hostHealth.value.memory || 0
  if (memory > 95) return 'quick-stat--danger'
  if (memory > 85) return 'quick-stat--warning'
  return 'quick-stat--success'
})

const getApiClass = computed(() => {
  const errorRate = apiHealth.value.errorRate || 0
  if (errorRate > 5) return 'quick-stat--danger'
  if (errorRate > 2) return 'quick-stat--warning'
  return 'quick-stat--success'
})
</script>

<style scoped>
.system-health-section {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  gap: 0;
}

/* Header */
.health-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
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
.title-icon--danger { background: #f44336; animation: pulse-danger 1s ease-in-out infinite; }
.title-icon--gray { background: #9E9E9E; }

@keyframes pulse-danger {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.header-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
}

.status-text {
  font-weight: 600;
}

.status-separator {
  color: rgba(var(--v-theme-on-surface), 0.3);
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 4px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.connection-status--live {
  color: #4CAF50;
}

.connection-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.connection-status--live .connection-dot {
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

/* Quick Stats */
.header-stats {
  display: flex;
  gap: 12px;
}

.quick-stat {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  transition: all 0.2s ease;
}

.quick-stat--success {
  background: rgba(76, 175, 80, 0.1);
  color: #4CAF50;
}

.quick-stat--warning {
  background: rgba(255, 152, 0, 0.1);
  color: #FF9800;
}

.quick-stat--danger {
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
}

.quick-stat__value {
  font-size: 0.85rem;
  font-weight: 700;
}

.quick-stat__label {
  font-size: 0.65rem;
  opacity: 0.8;
  text-transform: uppercase;
}

/* Tab Navigation */
.tab-nav {
  display: flex;
  gap: 4px;
  padding: 8px 16px;
  background: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-size: 0.8rem;
  font-weight: 500;
  transition: all 0.15s ease;
  position: relative;
}

.tab-btn:hover {
  background: rgba(var(--v-theme-primary), 0.06);
  color: rgba(var(--v-theme-on-surface), 0.9);
}

.tab-btn--active {
  background: rgba(var(--v-theme-primary), 0.12);
  color: rgb(var(--v-theme-primary));
}

.tab-btn__icon {
  opacity: 0.8;
}

.tab-btn--active .tab-btn__icon {
  opacity: 1;
}

.tab-btn__indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-left: 4px;
}

.tab-btn__indicator--success {
  background: #4CAF50;
  animation: pulse-dot 2s ease-in-out infinite;
}

/* Tab Content */
.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: rgba(var(--v-theme-on-surface), 0.02);
}

/* Responsive */
@media (max-width: 900px) {
  .health-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .header-stats {
    width: 100%;
    justify-content: flex-start;
  }

  .tab-nav {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .tab-btn__label {
    display: none;
  }

  .tab-btn {
    padding: 8px 12px;
  }
}

@media (max-width: 600px) {
  .quick-stat__label {
    display: none;
  }

  .quick-stat {
    padding: 6px 10px;
  }
}
</style>
