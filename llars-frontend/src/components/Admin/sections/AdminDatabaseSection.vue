<template>
  <div class="db-explorer">
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-database</v-icon>
        DB Explorer
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

        <LBtn prepend-icon="mdi-refresh" variant="tonal" @click="refreshTables">
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

        <v-row>
          <v-col cols="12" md="5">
            <v-skeleton-loader v-if="isLoading('tables')" type="text" />
            <v-select
              v-else
              v-model="selectedTable"
              :items="tableOptions"
              label="Tabelle"
              variant="outlined"
              density="comfortable"
              hide-details
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field
              v-model.number="limit"
              type="number"
              label="Limit"
              variant="outlined"
              density="comfortable"
              hide-details
              min="1"
              max="200"
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="search"
              label="Suche"
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="comfortable"
              hide-details
              clearable
            />
          </v-col>
        </v-row>

        <div class="d-flex flex-wrap ga-2 mt-3">
          <v-chip variant="tonal" density="compact">
            Rows: {{ rows.length }}
          </v-chip>
          <v-chip v-if="orderBy" variant="tonal" density="compact">
            Order: {{ orderBy }} DESC
          </v-chip>
          <v-chip v-if="polledAtLabel" variant="tonal" density="compact">
            Updated: {{ polledAtLabel }}
          </v-chip>
        </div>
      </v-card-text>
    </v-card>

    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-table</v-icon>
        Daten
        <v-spacer />
        <LBtn prepend-icon="mdi-sync" variant="primary" @click="resubscribe">
          Verbinden
        </LBtn>
      </v-card-title>
      <v-divider />
      <v-card-text>
        <v-skeleton-loader v-if="isLoading('table')" type="table" height="520" />

        <v-alert
          v-else-if="!selectedTable"
          type="info"
          variant="tonal"
          density="compact"
        >
          Bitte eine Tabelle auswählen.
        </v-alert>

        <div v-else class="db-table">
          <v-data-table
            :headers="headers"
            :items="filteredRows"
            :items-per-page="25"
            density="compact"
            fixed-header
            height="520"
            class="elevation-0"
          >
            <template v-slot:no-data>
              <v-alert type="info" variant="tonal" density="compact">
                Keine Daten vorhanden.
              </v-alert>
            </template>
          </v-data-table>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { io } from 'socket.io-client'
import { useAuth } from '@/composables/useAuth'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'

const auth = useAuth()
const { isLoading, setLoading } = useSkeletonLoading(['tables', 'table'])

const connectionState = ref('disconnected') // disconnected|connecting|connected|error
const errorMessage = ref('')

const tables = ref([])
const selectedTable = ref(null)
const limit = ref(50)
const search = ref('')

const columns = ref([])
const rows = ref([])
const orderBy = ref(null)
const polledAt = ref(null)

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

const tableOptions = computed(() => (tables.value || []).map((t) => ({ title: t, value: t })))

const headers = computed(() => {
  return (columns.value || []).map((c) => ({ title: c, key: c, sortable: false }))
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
    return new Date(polledAt.value).toLocaleString()
  } catch {
    return ''
  }
})

const refreshTables = () => {
  if (!socket.value) return
  setLoading('tables', true)
  socket.value.emit('db:get_tables')
}

const unsubscribe = (table) => {
  if (!socket.value) return
  if (!table) return
  socket.value.emit('db:unsubscribe_table', { table })
}

const resubscribe = () => {
  if (!socket.value) return
  if (!selectedTable.value) return
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
    transports: ['websocket', 'polling'],
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
  })

  s.on('db:tables', (payload) => {
    const list = Array.isArray(payload?.tables) ? payload.tables : []
    tables.value = list
    setLoading('tables', false)

    if (!selectedTable.value && list.length > 0) {
      selectedTable.value = list[0]
    }
  })

  s.on('db:table', (payload) => {
    if (!payload?.ok) {
      errorMessage.value = payload?.error || 'DB Snapshot fehlgeschlagen'
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
.db-table :deep(.v-table__wrapper) {
  overflow-x: auto;
}
</style>
