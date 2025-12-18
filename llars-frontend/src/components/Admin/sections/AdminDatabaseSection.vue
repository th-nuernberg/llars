<template>
  <div class="db-explorer">
    <!-- Header -->
    <div class="explorer-header">
      <div class="header-left">
        <v-icon size="24">mdi-database</v-icon>
        <h2>DB Explorer</h2>
        <LTag :variant="connectionVariant" :prepend-icon="connectionIcon" size="small">
          {{ connectionLabel }}
        </LTag>
        <div v-if="connectionState === 'connected'" class="live-pulse"></div>
      </div>
      <div class="header-right">
        <LBtn prepend-icon="mdi-refresh" variant="tonal" size="small" @click="refreshTables">
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
    <div class="explorer-content">
      <!-- Sidebar: Table List -->
      <div class="sidebar">
        <div class="sidebar-header">
          <v-icon size="18">mdi-table-multiple</v-icon>
          <span>Tabellen</span>
          <LTag variant="gray" size="small" class="ml-auto">{{ tables.length }}</LTag>
        </div>

        <div class="table-search">
          <v-text-field
            v-model="tableSearch"
            placeholder="Tabelle suchen..."
            prepend-inner-icon="mdi-magnify"
            variant="outlined"
            density="compact"
            hide-details
            clearable
          />
        </div>

        <div class="table-list">
          <v-skeleton-loader v-if="isLoading('tables')" type="list-item@8" />
          <template v-else>
            <div
              v-for="table in filteredTables"
              :key="table"
              :class="['table-item', { 'table-item--active': selectedTable === table }]"
              @click="selectTable(table)"
            >
              <v-icon size="16" class="table-icon">mdi-table</v-icon>
              <span class="table-name">{{ table }}</span>
              <v-icon v-if="selectedTable === table" size="14" class="active-icon">mdi-chevron-right</v-icon>
            </div>
            <div v-if="filteredTables.length === 0" class="empty-tables">
              <v-icon size="24">mdi-table-off</v-icon>
              <span>Keine Tabellen gefunden</span>
            </div>
          </template>
        </div>
      </div>

      <!-- Main: Data View -->
      <div class="data-view">
        <!-- Controls Bar -->
        <div class="controls-bar">
          <div class="control-group">
            <label class="control-label">Tabelle</label>
            <div class="selected-table">
              <v-icon size="16">mdi-table</v-icon>
              <span>{{ selectedTable || 'Keine ausgewählt' }}</span>
            </div>
          </div>

          <div class="control-group">
            <label class="control-label">Limit</label>
            <v-text-field
              v-model.number="limit"
              type="number"
              variant="outlined"
              density="compact"
              hide-details
              min="1"
              max="200"
              class="limit-field"
            />
          </div>

          <div class="control-group control-group--grow">
            <label class="control-label">Suche</label>
            <v-text-field
              v-model="search"
              placeholder="In Daten suchen..."
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              clearable
            />
          </div>

          <LBtn prepend-icon="mdi-sync" variant="primary" size="small" @click="resubscribe">
            Laden
          </LBtn>
        </div>

        <!-- Stats Bar -->
        <div class="stats-bar">
          <LTag variant="info" size="small" prepend-icon="mdi-table-row">
            {{ filteredRows.length }} Zeilen
          </LTag>
          <LTag v-if="orderBy" variant="secondary" size="small" prepend-icon="mdi-sort-descending">
            {{ orderBy }} DESC
          </LTag>
          <LTag v-if="polledAtLabel" variant="gray" size="small" prepend-icon="mdi-clock-outline">
            {{ polledAtLabel }}
          </LTag>
          <LTag v-if="columns.length > 0" variant="gray" size="small" prepend-icon="mdi-view-column">
            {{ columns.length }} Spalten
          </LTag>
        </div>

        <!-- Data Table -->
        <div class="data-table-container">
          <v-skeleton-loader v-if="isLoading('table')" type="table" class="skeleton-table" />

          <div v-else-if="!selectedTable" class="empty-state">
            <v-icon size="64" class="empty-icon">mdi-table-arrow-left</v-icon>
            <h3>Tabelle auswählen</h3>
            <p>Wähle eine Tabelle aus der Liste um die Daten anzuzeigen</p>
          </div>

          <div v-else-if="rows.length === 0" class="empty-state">
            <v-icon size="64" class="empty-icon">mdi-database-off</v-icon>
            <h3>Keine Daten</h3>
            <p>Die Tabelle <strong>{{ selectedTable }}</strong> enthält keine Einträge</p>
          </div>

          <div v-else class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th v-for="col in columns" :key="col" class="data-th">
                    {{ col }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, idx) in filteredRows" :key="idx" class="data-row">
                  <td v-for="col in columns" :key="col" class="data-td">
                    <span class="cell-content" :title="formatCell(row[col])">
                      {{ formatCell(row[col]) }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { io } from 'socket.io-client'
import { useAuth } from '@/composables/useAuth'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'

const socketioEnableWebsocket = String(import.meta.env.VITE_SOCKETIO_ENABLE_WEBSOCKET || '').toLowerCase() === 'true'
const socketioTransports = socketioEnableWebsocket ? ['polling', 'websocket'] : ['polling']

const auth = useAuth()
const { isLoading, setLoading } = useSkeletonLoading(['tables', 'table'])

const connectionState = ref('disconnected')
const errorMessage = ref('')

const tables = ref([])
const selectedTable = ref(null)
const tableSearch = ref('')
const limit = ref(50)
const search = ref('')

const columns = ref([])
const rows = ref([])
const orderBy = ref(null)
const polledAt = ref(null)

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

const filteredTables = computed(() => {
  const q = String(tableSearch.value || '').trim().toLowerCase()
  if (!q) return tables.value
  return tables.value.filter(t => t.toLowerCase().includes(q))
})

const filteredRows = computed(() => {
  const q = String(search.value || '').trim().toLowerCase()
  if (!q) return rows.value
  return (rows.value || []).filter((r) => {
    try {
      return JSON.stringify(r).toLowerCase().includes(q)
    } catch {
      return false
    }
  })
})

const polledAtLabel = computed(() => {
  if (!polledAt.value) return ''
  try {
    return new Date(polledAt.value).toLocaleTimeString('de-DE', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return ''
  }
})

const formatCell = (value) => {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value)
    } catch {
      return String(value)
    }
  }
  const str = String(value)
  if (str.length > 100) return str.substring(0, 100) + '...'
  return str
}

const selectTable = (table) => {
  if (selectedTable.value === table) return
  selectedTable.value = table
}

const refreshTables = () => {
  if (!socket.value) return
  setLoading('tables', true)
  socket.value.emit('db:get_tables')
}

const unsubscribe = (table) => {
  if (!socket.value || !table) return
  socket.value.emit('db:unsubscribe_table', { table })
}

const resubscribe = () => {
  if (!socket.value || !selectedTable.value) return
  setLoading('table', true)
  socket.value.emit('db:subscribe_table', { table: selectedTable.value, limit: Number(limit.value || 50) })
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
    transports: socketioTransports,
    upgrade: socketioEnableWebsocket,
    reconnection: true,
    reconnectionAttempts: Infinity,
    timeout: 30000,
    pingTimeout: 120000,
    pingInterval: 30000,
    query: { token }
  })

  socket.value = s

  s.on('connect', () => {
    connectionState.value = 'connected'
    refreshTables()
  })

  s.on('disconnect', () => {
    connectionState.value = 'disconnected'
  })

  s.on('connect_error', (err) => {
    connectionState.value = 'error'
    errorMessage.value = err?.message || 'Socket Verbindung fehlgeschlagen'
  })

  s.on('db:error', (payload) => {
    errorMessage.value = payload?.message || 'DB Fehler'
    setLoading('table', false)
    setLoading('tables', false)
  })

  s.on('db:tables', (payload) => {
    const list = Array.isArray(payload?.tables) ? payload.tables : []
    tables.value = list.sort((a, b) => a.localeCompare(b))
    setLoading('tables', false)

    if (!selectedTable.value && list.length > 0) {
      selectedTable.value = list[0]
    }
  })

  s.on('db:table', (payload) => {
    if (!payload?.ok) {
      errorMessage.value = payload?.error || 'DB Snapshot fehlgeschlagen'
      setLoading('table', false)
      return
    }
    if (payload.table !== selectedTable.value) return

    errorMessage.value = ''
    columns.value = Array.isArray(payload.columns) ? payload.columns : []
    rows.value = Array.isArray(payload.rows) ? payload.rows : []
    orderBy.value = payload.order_by || null
    polledAt.value = payload.polled_at ? payload.polled_at * 1000 : Date.now()
    setLoading('table', false)
  })
}

const disconnectSocket = () => {
  try {
    unsubscribe(selectedTable.value)
  } catch {
    // ignore
  }
  socket.value?.disconnect()
  socket.value = null
}

watch(selectedTable, (newTable, oldTable) => {
  if (oldTable) unsubscribe(oldTable)
  rows.value = []
  columns.value = []
  orderBy.value = null
  polledAt.value = null

  if (newTable) {
    resubscribe()
  }
})

watch(limit, () => {
  if (selectedTable.value) resubscribe()
})

onMounted(() => {
  connectSocket()
})

onBeforeUnmount(() => {
  disconnectSocket()
})
</script>

<style scoped>
.db-explorer {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px;
  gap: 12px;
}

/* Header */
.explorer-header {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--llars-gradient-secondary);
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
.explorer-content {
  flex: 1;
  display: flex;
  gap: 16px;
  min-height: 0;
  overflow: hidden;
}

/* Sidebar */
.sidebar {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius-sm);
  box-shadow: var(--llars-shadow-sm);
  overflow: hidden;
}

.sidebar-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  font-size: 0.85rem;
  font-weight: 600;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.table-search {
  flex-shrink: 0;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.table-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.table-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 0.85rem;
}

.table-item:hover {
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.table-item--active {
  background: var(--llars-gradient-primary-soft);
  color: var(--llars-primary);
  font-weight: 500;
}

.table-icon {
  opacity: 0.5;
}

.table-item--active .table-icon {
  opacity: 1;
  color: var(--llars-primary);
}

.table-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.active-icon {
  opacity: 0.7;
}

.empty-tables {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  gap: 8px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 0.8rem;
}

/* Data View */
.data-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
  gap: 10px;
}

/* Controls Bar */
.controls-bar {
  flex-shrink: 0;
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 12px 14px;
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius-sm);
  box-shadow: var(--llars-shadow-sm);
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.control-group--grow {
  flex: 1;
}

.control-label {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.selected-table {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(var(--v-theme-on-surface), 0.05);
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  min-width: 150px;
}

.limit-field {
  width: 80px;
}

/* Stats Bar */
.stats-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

/* Data Table Container */
.data-table-container {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius-sm);
  box-shadow: var(--llars-shadow-sm);
  overflow: hidden;
}

.skeleton-table {
  flex: 1;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  gap: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.empty-icon {
  opacity: 0.3;
}

.empty-state h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.empty-state p {
  margin: 0;
  font-size: 0.875rem;
  text-align: center;
}

/* Table Wrapper */
.table-wrapper {
  flex: 1;
  overflow: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.data-th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: linear-gradient(180deg, rgb(var(--v-theme-surface)) 0%, rgba(var(--v-theme-surface), 0.98) 100%);
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  border-bottom: 2px solid rgba(var(--v-border-color), var(--v-border-opacity));
  white-space: nowrap;
}

.data-row {
  transition: background-color 0.15s ease;
}

.data-row:hover {
  background: rgba(var(--v-theme-primary), 0.04);
}

.data-row:nth-child(even) {
  background: rgba(var(--v-theme-on-surface), 0.02);
}

.data-row:nth-child(even):hover {
  background: rgba(var(--v-theme-primary), 0.06);
}

.data-td {
  padding: 8px 12px;
  border-bottom: 1px solid rgba(var(--v-border-color), calc(var(--v-border-opacity) * 0.5));
  max-width: 300px;
}

.cell-content {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Mono', monospace;
  font-size: 0.75rem;
}

/* Scrollbars */
.table-list::-webkit-scrollbar,
.table-wrapper::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.table-list::-webkit-scrollbar-track,
.table-wrapper::-webkit-scrollbar-track {
  background: transparent;
}

.table-list::-webkit-scrollbar-thumb,
.table-wrapper::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 3px;
}

.table-list::-webkit-scrollbar-thumb:hover,
.table-wrapper::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-on-surface), 0.25);
}

/* Responsive */
@media (max-width: 900px) {
  .explorer-content {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    max-height: 200px;
  }

  .controls-bar {
    flex-wrap: wrap;
  }

  .control-group--grow {
    flex: 1 1 100%;
  }
}
</style>
