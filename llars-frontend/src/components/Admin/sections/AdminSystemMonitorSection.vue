<template>
  <div class="system-monitor">
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-monitor-dashboard</v-icon>
        System Monitor
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
          :loading="reloading"
          @click="reload"
          class="mr-2"
        >
          Neu laden
        </LBtn>

        <LBtn
          :prepend-icon="paused ? 'mdi-play' : 'mdi-pause'"
          variant="tonal"
          @click="togglePause"
          class="mr-2"
        >
          {{ paused ? 'Live' : 'Pause' }}
        </LBtn>

        <LBtn
          prepend-icon="mdi-trash-can-outline"
          variant="tonal"
          @click="clear"
        >
          Leeren
        </LBtn>
      </v-card-title>
      <v-divider />
      <v-card-text>
        <v-row>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="search"
              label="Suche (Typ, Message, User)"
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="comfortable"
              hide-details
              clearable
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="severityFilter"
              :items="severityOptions"
              label="Severity"
              variant="outlined"
              density="comfortable"
              hide-details
              clearable
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-switch
              v-model="autoScroll"
              color="primary"
              hide-details
              label="Auto-Scroll"
            />
          </v-col>
          <v-col cols="12" md="2" class="d-flex align-center justify-end">
            <v-chip variant="tonal" density="compact">
              {{ filteredEvents.length }} Events
            </v-chip>
          </v-col>
        </v-row>

        <v-skeleton-loader
          v-if="isLoading('table')"
          type="table"
          height="420"
          class="mt-3"
        />

        <div v-else class="mt-3">
          <v-data-table
            ref="tableRef"
            :items="filteredEvents"
            :headers="headers"
            item-key="id"
            density="compact"
            :items-per-page="50"
            class="events-table"
            fixed-header
            height="520"
          >
            <template v-slot:item.created_at="{ item }">
              <span class="text-medium-emphasis">{{ formatTime(item.created_at) }}</span>
            </template>

            <template v-slot:item.severity="{ item }">
              <v-chip :color="severityColor(item.severity)" density="compact" variant="tonal">
                {{ item.severity }}
              </v-chip>
            </template>

            <template v-slot:item.username="{ item }">
              <span class="font-weight-medium">{{ item.username || '-' }}</span>
            </template>

            <template v-slot:item.message="{ item }">
              <div class="event-message">
                <div class="event-message__main">{{ item.message }}</div>
                <div v-if="item.entity_type || item.entity_id" class="event-message__meta text-caption text-medium-emphasis">
                  {{ item.entity_type || '' }}{{ item.entity_type && item.entity_id ? ':' : '' }}{{ item.entity_id || '' }}
                </div>
              </div>
            </template>

            <template v-slot:no-data>
              <v-alert type="info" variant="tonal" density="compact">
                Keine Events vorhanden.
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
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'

const auth = useAuth()
const { isLoading, withLoading } = useSkeletonLoading(['table'])

const headers = [
  { title: 'Zeit', key: 'created_at', width: 180 },
  { title: 'Severity', key: 'severity', width: 120 },
  { title: 'Typ', key: 'event_type', width: 220 },
  { title: 'User', key: 'username', width: 160 },
  { title: 'Message', key: 'message' }
]

const events = ref([])
const lastEventId = ref(0)
const paused = ref(false)
const autoScroll = ref(true)
const tableRef = ref(null)
const search = ref('')
const severityFilter = ref(null)
const reloading = ref(false)

const connectionState = ref('disconnected') // disconnected|connecting|connected|error
const streamAbortController = ref(null)
let reconnectTimer = null

const severityOptions = [
  { title: 'Alle', value: null },
  { title: 'success', value: 'success' },
  { title: 'info', value: 'info' },
  { title: 'warning', value: 'warning' },
  { title: 'error', value: 'error' },
  { title: 'critical', value: 'critical' }
]

const connectionLabel = computed(() => {
  if (paused.value) return 'pausiert'
  if (connectionState.value === 'connected') return 'live'
  if (connectionState.value === 'connecting') return 'verbinde...'
  if (connectionState.value === 'error') return 'fehler'
  return 'offline'
})

const connectionColor = computed(() => {
  if (paused.value) return 'grey'
  if (connectionState.value === 'connected') return 'success'
  if (connectionState.value === 'connecting') return 'warning'
  if (connectionState.value === 'error') return 'error'
  return 'grey'
})

const connectionIcon = computed(() => {
  if (paused.value) return 'mdi-pause-circle-outline'
  if (connectionState.value === 'connected') return 'mdi-wifi'
  if (connectionState.value === 'connecting') return 'mdi-wifi-sync'
  if (connectionState.value === 'error') return 'mdi-wifi-off'
  return 'mdi-wifi-off'
})

const severityColor = (severity) => {
  const s = String(severity || '').toLowerCase()
  if (s === 'success') return 'success'
  if (s === 'warning') return 'warning'
  if (s === 'error' || s === 'critical') return 'error'
  return 'info'
}

const formatTime = (iso) => {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

const filteredEvents = computed(() => {
  const q = String(search.value || '').trim().toLowerCase()
  const sev = severityFilter.value

  return events.value.filter((e) => {
    if (sev && String(e.severity || '').toLowerCase() !== sev) return false
    if (!q) return true

    const haystack = [
      e.event_type,
      e.message,
      e.username,
      e.entity_type,
      e.entity_id
    ].filter(Boolean).join(' ').toLowerCase()
    return haystack.includes(q)
  })
})

const addEvent = (event) => {
  if (!event?.id) return
  if (event.id <= lastEventId.value) return
  lastEventId.value = event.id

  events.value.unshift(event)
  if (events.value.length > 500) {
    events.value.length = 500
  }

  if (autoScroll.value) {
    requestAnimationFrame(() => {
      const root = tableRef.value?.$el || tableRef.value
      const wrapper = root?.querySelector?.('.v-table__wrapper')
      if (wrapper) wrapper.scrollTop = 0
    })
  }
}

const stopStream = () => {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  if (streamAbortController.value) {
    streamAbortController.value.abort()
    streamAbortController.value = null
  }
  if (!paused.value) connectionState.value = 'disconnected'
}

const scheduleReconnect = () => {
  if (paused.value) return
  if (reconnectTimer) return
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    startStream()
  }, 2000)
}

const parseAndHandleSseChunk = (chunk, state) => {
  state.buffer += chunk

  const parts = state.buffer.split('\n\n')
  state.buffer = parts.pop() || ''

  for (const part of parts) {
    const lines = part.split('\n')
    let eventName = null
    let id = null
    const dataLines = []

    for (const line of lines) {
      if (line.startsWith('event:')) eventName = line.slice(6).trim()
      else if (line.startsWith('id:')) id = Number(line.slice(3).trim())
      else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim())
    }

    if (eventName === 'ping') continue
    const dataStr = dataLines.join('\n').trim()
    if (!dataStr) continue

    try {
      const parsed = JSON.parse(dataStr)
      if (id && parsed && !parsed.id) parsed.id = id
      addEvent(parsed)
    } catch {
      // ignore invalid payloads
    }
  }
}

const startStream = async () => {
  if (paused.value) return
  stopStream()

  const token = auth.getToken()
  if (!token) {
    connectionState.value = 'error'
    return
  }

  connectionState.value = 'connecting'
  const controller = new AbortController()
  streamAbortController.value = controller

  const streamState = { buffer: '' }

  try {
    const url = `/api/admin/system/events/stream?after_id=${encodeURIComponent(String(lastEventId.value || 0))}`
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`
      },
      signal: controller.signal
    })

    if (!response.ok || !response.body) {
      connectionState.value = 'error'
      scheduleReconnect()
      return
    }

    connectionState.value = 'connected'

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      if (controller.signal.aborted) break
      parseAndHandleSseChunk(decoder.decode(value, { stream: true }), streamState)
    }

    if (!controller.signal.aborted) {
      connectionState.value = 'error'
      scheduleReconnect()
    }
  } catch (e) {
    if (!controller.signal.aborted) {
      connectionState.value = 'error'
      scheduleReconnect()
    }
  }
}

const loadInitial = async () => {
  await withLoading('table', async () => {
    const { data } = await axios.get('/api/admin/system/events', { params: { limit: 200 } })
    const list = Array.isArray(data?.events) ? data.events : []
    events.value = list.sort((a, b) => (b.id || 0) - (a.id || 0))
    lastEventId.value = events.value.length ? events.value[0].id : 0
  })
}

const reload = async () => {
  reloading.value = true
  try {
    await loadInitial()
    if (!paused.value) startStream()
  } finally {
    reloading.value = false
  }
}

const clear = () => {
  events.value = []
  lastEventId.value = 0
}

const togglePause = () => {
  paused.value = !paused.value
}

watch(paused, (val) => {
  if (val) {
    stopStream()
    connectionState.value = 'disconnected'
  } else {
    startStream()
  }
})

onMounted(async () => {
  await loadInitial()
  startStream()
})

onBeforeUnmount(() => {
  stopStream()
})
</script>

<style scoped>
.events-table :deep(.v-data-table__td) {
  vertical-align: top;
}

.event-message__main {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.event-message__meta {
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
