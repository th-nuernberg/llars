<template>
  <div class="presence-section">
    <div class="presence-header">
      <div class="header-title">
        <div class="title-icon" :class="connectionIconClass">
          <LIcon size="20" color="white">mdi-account-check</LIcon>
        </div>
        <div>
          <h2 class="text-subtitle-1 font-weight-bold">{{ t('adminPresence.title') }}</h2>
          <div class="header-status">
            <span class="status-text" :class="statusTextClass">{{ connectionLabel }}</span>
            <span v-if="connectionState === 'connected'" class="live-dot" />
          </div>
        </div>
      </div>

      <div class="header-stats">
        <div class="stat-chip stat-chip--active">
          <LIcon size="14">mdi-lightning-bolt</LIcon>
          <span>{{ counts.active }}</span>
        </div>
        <div class="stat-chip stat-chip--online">
          <LIcon size="14">mdi-circle</LIcon>
          <span>{{ counts.online }}</span>
        </div>
        <div class="stat-chip stat-chip--offline">
          <LIcon size="14">mdi-circle-off-outline</LIcon>
          <span>{{ counts.offline }}</span>
        </div>
      </div>
    </div>

    <div class="filters-bar">
      <div class="search-wrapper">
        <LIcon size="16" class="search-icon">mdi-magnify</LIcon>
        <input
          v-model="search"
          type="text"
          :placeholder="t('adminPresence.searchPlaceholder')"
          class="search-input"
        />
        <button v-if="search" class="search-clear" @click="search = ''">
          <LIcon size="14">mdi-close</LIcon>
        </button>
      </div>

      <div class="filter-chips">
        <button
          v-for="option in statusFilters"
          :key="option.value"
          class="filter-chip"
          :class="{ 'filter-chip--active': statusFilter === option.value, [`filter-chip--${option.variant}`]: true }"
          @click="statusFilter = statusFilter === option.value ? null : option.value"
        >
          <LIcon size="12">{{ option.icon }}</LIcon>
          <span>{{ option.label }}</span>
        </button>
      </div>
    </div>

    <div class="presence-table-wrapper">
      <LSkeleton v-if="loading" type="table" :count="8" :columns="4" />

      <div v-else class="presence-table">
        <table>
          <thead>
            <tr>
              <th class="col-user">{{ t('adminPresence.user') }}</th>
              <th class="col-status">{{ t('adminPresence.statusLabel') }}</th>
              <th class="col-last-active">{{ t('adminPresence.lastActive') }}</th>
              <th class="col-last-seen">{{ t('adminPresence.lastSeen') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in filteredUsers" :key="user.user_id">
              <td class="col-user">
                <div class="user-cell">
                  <span class="user-dot" :class="`user-dot--${user.status}`" />
                  <span class="user-name">{{ user.username }}</span>
                </div>
              </td>
              <td class="col-status">
                <LTag :variant="statusVariant(user.status)" size="small">
                  {{ statusLabel(user.status) }}
                </LTag>
              </td>
              <td class="col-last-active">
                <span v-if="user.last_active_at" :title="formatFullTime(user.last_active_at)">
                  {{ formatRelativeTime(user.last_active_at) }}
                </span>
                <span v-else class="text-medium-emphasis">-</span>
              </td>
              <td class="col-last-seen">
                <span v-if="user.last_seen_at" :title="formatFullTime(user.last_seen_at)">
                  {{ formatRelativeTime(user.last_seen_at) }}
                </span>
                <span v-else class="text-medium-emphasis">-</span>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="filteredUsers.length === 0" class="empty-state">
          <LIcon size="40" class="text-medium-emphasis">mdi-account-off-outline</LIcon>
          <span class="text-medium-emphasis">{{ t('adminPresence.empty') }}</span>
        </div>
      </div>
    </div>

    <div v-if="errorMessage" class="error-banner">
      <LIcon size="16" class="mr-1">mdi-alert-circle</LIcon>
      <span>{{ errorMessage }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getSocket } from '@/services/socketService'

const { t } = useI18n()

const users = ref([])
const search = ref('')
const statusFilter = ref(null)
const loading = ref(true)
const errorMessage = ref('')
const connectionState = ref('disconnected')

let socket = null

const handleConnect = () => {
  connectionState.value = 'connected'
  subscribe()
}

const handleDisconnect = () => {
  connectionState.value = 'disconnected'
}

const handleState = (data) => {
  applyUsers(data?.users || [])
  loading.value = false
  errorMessage.value = ''
}

const handleUpdate = (payload) => {
  applyUserUpdate(payload)
}

const handleError = (payload) => {
  errorMessage.value = payload?.message || t('adminPresence.errors.generic')
  loading.value = false
}

const statusFilters = [
  { value: 'active', label: t('adminPresence.status.active'), icon: 'mdi-lightning-bolt', variant: 'success' },
  { value: 'online', label: t('adminPresence.status.online'), icon: 'mdi-circle', variant: 'info' },
  { value: 'offline', label: t('adminPresence.status.offline'), icon: 'mdi-circle-off-outline', variant: 'warning' }
]

const connectionLabel = computed(() => {
  if (connectionState.value === 'connected') return t('adminPresence.connection.live')
  if (connectionState.value === 'connecting') return t('adminPresence.connection.connecting')
  return t('adminPresence.connection.disconnected')
})

const connectionIconClass = computed(() => ({
  'status-icon--live': connectionState.value === 'connected',
  'status-icon--warning': connectionState.value === 'connecting',
  'status-icon--offline': connectionState.value !== 'connected'
}))

const statusTextClass = computed(() => ({
  'text-success': connectionState.value === 'connected',
  'text-warning': connectionState.value === 'connecting',
  'text-error': connectionState.value === 'disconnected'
}))

const counts = computed(() => {
  const result = { active: 0, online: 0, offline: 0 }
  users.value.forEach((user) => {
    if (user.status === 'active') result.active += 1
    else if (user.status === 'online') result.online += 1
    else result.offline += 1
  })
  return result
})

const applyUsers = (list) => {
  users.value = Array.isArray(list) ? list : []
}

const applyUserUpdate = (payload) => {
  if (!payload?.user_id) return
  const index = users.value.findIndex((u) => u.user_id === payload.user_id)
  if (index >= 0) {
    users.value.splice(index, 1, { ...users.value[index], ...payload })
  } else {
    users.value.unshift(payload)
  }
}

const filteredUsers = computed(() => {
  const q = String(search.value || '').trim().toLowerCase()
  const status = statusFilter.value
  const list = users.value.filter((user) => {
    if (status && user.status !== status) return false
    if (!q) return true
    return String(user.username || '').toLowerCase().includes(q)
  })
  return list.sort((a, b) => {
    const aTs = Date.parse(a.last_active_at || a.last_seen_at || 0) || 0
    const bTs = Date.parse(b.last_active_at || b.last_seen_at || 0) || 0
    return bTs - aTs
  })
})

const statusVariant = (status) => {
  if (status === 'active') return 'success'
  if (status === 'online') return 'info'
  return 'warning'
}

const statusLabel = (status) => {
  if (status === 'active') return t('adminPresence.status.active')
  if (status === 'online') return t('adminPresence.status.online')
  return t('adminPresence.status.offline')
}

const formatRelativeTime = (iso) => {
  const date = new Date(iso)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return t('adminPresence.time.justNow')
  if (diffMins < 60) return t('adminPresence.time.minutes', { count: diffMins })
  if (diffHours < 24) return t('adminPresence.time.hours', { count: diffHours })
  if (diffDays < 7) return t('adminPresence.time.days', { count: diffDays })
  return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' })
}

const formatFullTime = (iso) => {
  try {
    return new Date(iso).toLocaleString('de-DE', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    })
  } catch {
    return iso
  }
}

const subscribe = () => {
  if (!socket) return
  connectionState.value = socket.connected ? 'connected' : 'connecting'
  socket.emit('presence:subscribe')
}

const setupSocket = () => {
  socket = getSocket()
  if (!socket) return

  socket.on('connect', handleConnect)
  socket.on('disconnect', handleDisconnect)
  socket.on('presence:state', handleState)
  socket.on('presence:update', handleUpdate)
  socket.on('presence:error', handleError)

  if (socket.connected) {
    subscribe()
  }
}

const cleanupSocket = () => {
  if (!socket) return
  socket.emit('presence:unsubscribe')
  socket.off('connect', handleConnect)
  socket.off('disconnect', handleDisconnect)
  socket.off('presence:state', handleState)
  socket.off('presence:update', handleUpdate)
  socket.off('presence:error', handleError)
  socket = null
}

onMounted(setupSocket)
onUnmounted(cleanupSocket)
</script>

<style scoped>
.presence-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.presence-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #42a5f5, #1e88e5);
}

.status-icon--live {
  background: linear-gradient(135deg, #2e7d32, #43a047);
}

.status-icon--warning {
  background: linear-gradient(135deg, #f9a825, #f57f17);
}

.status-icon--offline {
  background: linear-gradient(135deg, #607d8b, #455a64);
}

.header-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #43a047;
  box-shadow: 0 0 0 4px rgba(67, 160, 71, 0.2);
}

.header-stats {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(96, 125, 139, 0.1);
  font-weight: 600;
}

.stat-chip--active {
  background: rgba(67, 160, 71, 0.12);
  color: #2e7d32;
}

.stat-chip--online {
  background: rgba(33, 150, 243, 0.12);
  color: #1e88e5;
}

.stat-chip--offline {
  background: rgba(96, 125, 139, 0.12);
  color: #546e7a;
}

.filters-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  justify-content: space-between;
}

.search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  background: rgba(96, 125, 139, 0.08);
  border-radius: 12px;
  padding: 6px 10px;
  min-width: 260px;
  flex: 1;
}

.search-input {
  border: none;
  outline: none;
  background: transparent;
  width: 100%;
  padding: 4px 8px;
  font-size: 0.9rem;
}

.search-icon {
  color: rgba(0, 0, 0, 0.54);
}

.search-clear {
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 2px;
}

.filter-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-chip {
  border: none;
  background: rgba(96, 125, 139, 0.08);
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 0.8rem;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #455a64;
}

.filter-chip--active {
  background: rgba(33, 150, 243, 0.2);
  color: #1e88e5;
}

.presence-table-wrapper {
  background: #fff;
  border-radius: 16px;
  padding: 12px;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
}

.presence-table table {
  width: 100%;
  border-collapse: collapse;
}

.presence-table th,
.presence-table td {
  text-align: left;
  padding: 12px 8px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.col-user {
  width: 35%;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #cfd8dc;
}

.user-dot--active {
  background: #43a047;
}

.user-dot--online {
  background: #1e88e5;
}

.user-dot--offline {
  background: #90a4ae;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px 12px;
}

.error-banner {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(244, 67, 54, 0.1);
  color: #c62828;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 0.85rem;
}

@media (max-width: 900px) {
  .presence-table-wrapper {
    padding: 8px;
  }

  .presence-table table,
  .presence-table thead {
    display: none;
  }

  .presence-table tbody tr {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 12px 8px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  }

  .presence-table tbody td {
    border: none;
    padding: 0;
  }
}
</style>
