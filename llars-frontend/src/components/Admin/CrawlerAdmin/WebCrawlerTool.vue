<template>
  <v-container fluid class="pa-0">
    <!-- Header with Status -->
    <v-card class="mb-4" variant="flat" color="transparent">
      <v-card-text class="d-flex justify-space-between align-center pa-0">
        <div>
          <h2 class="text-h5 font-weight-bold mb-1">Website Crawler</h2>
          <p class="text-body-2 text-medium-emphasis mb-0">
            Crawlen Sie Websites und erstellen Sie automatisch RAG-Collections
          </p>
        </div>
        <div class="d-flex align-center ga-2">
          <v-chip
            :color="socketConnected ? 'success' : 'error'"
            :variant="socketConnected ? 'flat' : 'outlined'"
            size="small"
            class="font-weight-medium"
          >
            <v-icon start size="14">{{ socketConnected ? 'mdi-wifi' : 'mdi-wifi-off' }}</v-icon>
            {{ socketConnected ? 'Live verbunden' : 'Offline' }}
          </v-chip>
          <v-btn
            icon="mdi-refresh"
            variant="text"
            size="small"
            :loading="loadingJobs"
            @click="loadJobs"
          />
        </div>
      </v-card-text>
    </v-card>

    <!-- Active Crawl Alert -->
    <v-slide-y-transition>
      <v-alert
        v-if="runningJobs.length > 0 && !watchingJob"
        type="info"
        variant="tonal"
        class="mb-4"
        prominent
        closable
      >
        <template v-slot:prepend>
          <v-progress-circular indeterminate size="24" width="2" />
        </template>
        <div class="d-flex justify-space-between align-center flex-wrap ga-2">
          <div>
            <span class="font-weight-bold">{{ runningJobs.length }} aktive{{ runningJobs.length > 1 ? ' Crawls' : 'r Crawl' }}</span>
            <span class="text-body-2 ml-2">- Klicken Sie auf "Live ansehen" um den Fortschritt zu verfolgen</span>
          </div>
          <v-btn
            color="primary"
            variant="flat"
            size="small"
            @click="watchJob(runningJobs[0])"
            prepend-icon="mdi-eye"
          >
            Live ansehen
          </v-btn>
        </div>
      </v-alert>
    </v-slide-y-transition>

    <v-row>
      <!-- Left Column: New Crawl Form -->
      <v-col cols="12" :md="watchingJob ? 5 : 6">
        <v-card elevation="2">
          <v-card-title class="d-flex align-center bg-primary text-white">
            <v-icon start>mdi-web-plus</v-icon>
            Neuen Crawl starten
          </v-card-title>
          <v-card-text class="pt-4">
            <!-- URLs Input -->
            <v-textarea
              v-model="crawlForm.urlsText"
              label="URLs zum Crawlen"
              placeholder="https://example.com&#10;https://docs.example.com"
              hint="Eine URL pro Zeile. Der Crawler folgt internen Links automatisch."
              persistent-hint
              rows="3"
              variant="outlined"
              density="comfortable"
              class="mb-3"
              :error="urlError !== null"
              :error-messages="urlError"
              @input="validateUrls"
            />

            <!-- Collection Name -->
            <v-text-field
              v-model="crawlForm.collectionName"
              label="Collection Name *"
              placeholder="z.B. Unternehmensdokumentation"
              variant="outlined"
              density="comfortable"
              class="mb-3"
              :rules="[v => !!v || 'Name ist erforderlich']"
            />

            <!-- Description -->
            <v-textarea
              v-model="crawlForm.description"
              label="Beschreibung (optional)"
              placeholder="Beschreibung der Dokumentensammlung..."
              rows="2"
              variant="outlined"
              density="comfortable"
              class="mb-3"
            />

            <!-- Settings -->
            <v-expansion-panels variant="accordion" class="mb-4">
              <v-expansion-panel>
                <v-expansion-panel-title>
                  <v-icon start size="small">mdi-tune</v-icon>
                  Erweiterte Einstellungen
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <v-row dense>
                    <v-col cols="6">
                      <v-text-field
                        v-model.number="crawlForm.maxPages"
                        label="Max. Seiten"
                        type="number"
                        min="1"
                        max="200"
                        variant="outlined"
                        density="compact"
                        hint="Pro Start-URL"
                        persistent-hint
                      />
                    </v-col>
                    <v-col cols="6">
                      <v-text-field
                        v-model.number="crawlForm.maxDepth"
                        label="Max. Tiefe"
                        type="number"
                        min="1"
                        max="5"
                        variant="outlined"
                        density="compact"
                        hint="Link-Ebenen"
                        persistent-hint
                      />
                    </v-col>
                  </v-row>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>

            <!-- Action Buttons -->
            <div class="d-flex ga-2">
              <v-btn
                color="primary"
                :loading="startingCrawl"
                :disabled="!canStartCrawl"
                @click="startBackgroundCrawl"
                prepend-icon="mdi-spider-web"
                variant="flat"
              >
                Crawl starten
              </v-btn>
              <v-btn
                variant="outlined"
                :loading="previewing"
                :disabled="!hasValidUrl"
                @click="previewUrl"
                prepend-icon="mdi-magnify"
              >
                Vorschau
              </v-btn>
            </div>
          </v-card-text>
        </v-card>

        <!-- Preview Card -->
        <v-slide-y-transition>
          <v-card v-if="preview" class="mt-4" elevation="2">
            <v-card-title class="bg-surface-variant">
              <v-icon start color="info">mdi-file-search</v-icon>
              Vorschau: {{ preview.title || 'Seite' }}
            </v-card-title>
            <v-card-text class="pt-3">
              <v-row dense>
                <v-col cols="6">
                  <div class="text-caption text-medium-emphasis">URL</div>
                  <div class="text-body-2 text-truncate">{{ preview.url }}</div>
                </v-col>
                <v-col cols="3">
                  <div class="text-caption text-medium-emphasis">Content</div>
                  <div class="text-body-2">{{ formatNumber(preview.content_length) }} Zeichen</div>
                </v-col>
                <v-col cols="3">
                  <div class="text-caption text-medium-emphasis">Links</div>
                  <div class="text-body-2">{{ preview.internal_links_count }} intern</div>
                </v-col>
              </v-row>
              <v-divider class="my-3" />
              <div class="text-caption text-medium-emphasis mb-1">Content-Vorschau:</div>
              <v-sheet color="grey-lighten-4" rounded class="pa-2" style="max-height: 120px; overflow-y: auto;">
                <pre class="text-caption" style="white-space: pre-wrap; margin: 0;">{{ preview.content_preview }}</pre>
              </v-sheet>
            </v-card-text>
          </v-card>
        </v-slide-y-transition>
      </v-col>

      <!-- Right Column: Live Session Viewer -->
      <v-col cols="12" :md="watchingJob ? 7 : 6">
        <v-card v-if="watchingJob" elevation="3" class="live-session-card">
          <!-- Header -->
          <v-card-title class="d-flex justify-space-between align-center bg-primary text-white py-3">
            <div class="d-flex align-center">
              <v-progress-circular
                v-if="watchingJob.status === 'running'"
                indeterminate
                size="20"
                width="2"
                class="mr-2"
              />
              <v-icon v-else :color="getStatusColor(watchingJob.status)" class="mr-2">
                {{ getStatusIcon(watchingJob.status) }}
              </v-icon>
              <span>Live Crawl Session</span>
            </div>
            <v-btn
              icon="mdi-close"
              variant="text"
              density="compact"
              @click="stopWatching"
            />
          </v-card-title>

          <v-card-text class="pt-4">
            <!-- Progress Section -->
            <div class="mb-4">
              <div class="d-flex justify-space-between align-center mb-2">
                <span class="text-body-2 font-weight-medium">Fortschritt</span>
                <span class="text-body-2">
                  <span class="font-weight-bold text-primary">{{ liveProgress.pages_crawled || 0 }}</span>
                  / {{ liveProgress.max_pages || '?' }} Seiten
                </span>
              </div>
              <v-progress-linear
                :model-value="progressPercent"
                :indeterminate="watchingJob.status === 'running' && !liveProgress.pages_crawled"
                :color="getStatusColor(watchingJob.status)"
                height="10"
                rounded
                striped
              />
            </div>

            <!-- Current URL Card -->
            <v-card
              v-if="liveProgress.current_url && watchingJob.status === 'running'"
              variant="tonal"
              color="info"
              class="mb-4"
            >
              <v-card-text class="py-2">
                <div class="d-flex align-center">
                  <v-icon class="mr-2 mdi-spin" size="small">mdi-loading</v-icon>
                  <div class="flex-grow-1 overflow-hidden">
                    <div class="text-caption text-medium-emphasis">Aktuell wird gecrawlt:</div>
                    <div class="text-body-2 font-weight-medium text-truncate">
                      {{ liveProgress.current_url }}
                    </div>
                  </div>
                </div>
                <div class="text-caption text-medium-emphasis mt-1">
                  Start-URL {{ liveProgress.current_url_index || 1 }} von {{ liveProgress.total_urls || 1 }}
                </div>
              </v-card-text>
            </v-card>

            <!-- Stats Row -->
            <v-row dense class="mb-4">
              <v-col cols="4">
                <v-card variant="tonal" color="primary" class="text-center pa-3">
                  <div class="text-h5 font-weight-bold">{{ liveProgress.pages_crawled || 0 }}</div>
                  <div class="text-caption">Seiten</div>
                </v-card>
              </v-col>
              <v-col cols="4">
                <v-card variant="tonal" color="success" class="text-center pa-3">
                  <div class="text-h5 font-weight-bold">{{ watchingJob.documents_created || 0 }}</div>
                  <div class="text-caption">Dokumente</div>
                </v-card>
              </v-col>
              <v-col cols="4">
                <v-card variant="tonal" color="warning" class="text-center pa-3">
                  <div class="text-h5 font-weight-bold">{{ watchingJob.errors?.length || 0 }}</div>
                  <div class="text-caption">Übersprungen</div>
                </v-card>
              </v-col>
            </v-row>

            <!-- Activity Log -->
            <div>
              <div class="d-flex justify-space-between align-center mb-2">
                <span class="text-body-2 font-weight-medium">Aktivitäts-Log</span>
                <v-chip size="x-small" color="primary" variant="flat">
                  {{ recentPages.length }} Einträge
                </v-chip>
              </div>
              <v-sheet
                color="grey-darken-4"
                rounded
                class="activity-log pa-2"
              >
                <div
                  v-for="(page, idx) in recentPages.slice().reverse().slice(0, 15)"
                  :key="idx"
                  class="log-entry d-flex align-center py-1"
                  :class="{ 'font-weight-bold': idx === 0 }"
                >
                  <v-icon size="x-small" color="success" class="mr-2">mdi-check-circle</v-icon>
                  <span class="text-truncate log-url">{{ page.url }}</span>
                </div>
                <div v-if="recentPages.length === 0" class="text-center text-medium-emphasis py-4">
                  <v-icon size="large" class="mb-2">mdi-spider-web</v-icon>
                  <div>Warte auf erste Seite...</div>
                </div>
              </v-sheet>
            </div>

            <!-- Completion/Error Messages -->
            <v-alert
              v-if="watchingJob.status === 'completed'"
              type="success"
              variant="tonal"
              class="mt-4"
            >
              <div class="d-flex justify-space-between align-center">
                <div>
                  <strong>Crawl erfolgreich abgeschlossen!</strong>
                  <div class="text-body-2">{{ watchingJob.documents_created }} Dokumente wurden erstellt.</div>
                </div>
                <v-btn
                  v-if="watchingJob.collection_id"
                  color="success"
                  variant="flat"
                  size="small"
                  @click="goToCollection(watchingJob.collection_id)"
                  prepend-icon="mdi-folder-open"
                >
                  Zur Collection
                </v-btn>
              </div>
            </v-alert>

            <v-alert
              v-if="watchingJob.status === 'failed'"
              type="error"
              variant="tonal"
              class="mt-4"
            >
              <strong>Crawl fehlgeschlagen</strong>
              <div class="text-body-2 mt-1">{{ watchingJob.error || 'Unbekannter Fehler' }}</div>
            </v-alert>
          </v-card-text>
        </v-card>

        <!-- Empty State -->
        <v-card v-else elevation="1" class="d-flex flex-column align-center justify-center text-center" min-height="400">
          <v-card-text>
            <v-icon size="80" color="primary" class="mb-4 opacity-50">mdi-spider-web</v-icon>
            <h3 class="text-h6 mb-2">Bereit zum Crawlen</h3>
            <p class="text-body-2 text-medium-emphasis mb-4">
              Starten Sie einen neuen Crawl oder wählen Sie einen<br>laufenden Job aus der Liste unten.
            </p>
            <v-btn
              v-if="runningJobs.length > 0"
              color="primary"
              variant="flat"
              @click="watchJob(runningJobs[0])"
              prepend-icon="mdi-eye"
            >
              Laufenden Crawl ansehen
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Jobs Table -->
    <v-card class="mt-4" elevation="2">
      <v-card-title class="d-flex justify-space-between align-center">
        <div class="d-flex align-center">
          <v-icon start>mdi-history</v-icon>
          Crawl-Verlauf
        </div>
        <v-btn
          icon="mdi-refresh"
          variant="text"
          size="small"
          :loading="loadingJobs"
          @click="loadJobs"
        />
      </v-card-title>
      <v-divider />
      <v-card-text class="pa-0">
        <v-skeleton-loader v-if="loadingJobs && jobs.length === 0" type="table-tbody" />
        <v-data-table
          v-else
          :headers="jobHeaders"
          :items="jobs"
          :items-per-page="5"
          density="comfortable"
          class="jobs-table"
          hover
          @click:row="(_, { item }) => onJobClick(item)"
        >
          <template v-slot:item.status="{ item }">
            <v-chip
              :color="getStatusColor(item.status)"
              size="small"
              :variant="item.status === 'running' ? 'elevated' : 'flat'"
              class="font-weight-medium"
            >
              <v-progress-circular
                v-if="item.status === 'running'"
                indeterminate
                size="12"
                width="2"
                class="mr-1"
              />
              <v-icon v-else start size="small">{{ getStatusIcon(item.status) }}</v-icon>
              {{ getStatusLabel(item.status) }}
            </v-chip>
          </template>
          <template v-slot:item.urls="{ item }">
            <div class="text-truncate" style="max-width: 250px;">
              {{ item.urls?.join(', ') || '-' }}
            </div>
          </template>
          <template v-slot:item.pages_crawled="{ item }">
            <span :class="{ 'font-weight-bold text-primary': item.status === 'running' }">
              {{ item.pages_crawled || 0 }}
            </span>
          </template>
          <template v-slot:item.documents_created="{ item }">
            <span :class="{ 'text-success': item.documents_created > 0 }">
              {{ item.documents_created || 0 }}
            </span>
          </template>
          <template v-slot:item.started_at="{ item }">
            {{ formatDate(item.started_at || item.queued_at) }}
          </template>
          <template v-slot:item.actions="{ item }">
            <div class="d-flex ga-1">
              <v-btn
                v-if="item.status === 'running' || item.status === 'queued'"
                icon="mdi-eye"
                variant="text"
                size="x-small"
                color="primary"
                @click.stop="watchJob(item)"
              >
                <v-icon>mdi-eye</v-icon>
                <v-tooltip activator="parent" location="top">Live ansehen</v-tooltip>
              </v-btn>
              <v-btn
                v-if="item.collection_id"
                icon="mdi-folder-open"
                variant="text"
                size="x-small"
                color="success"
                @click.stop="goToCollection(item.collection_id)"
              >
                <v-icon>mdi-folder-open</v-icon>
                <v-tooltip activator="parent" location="top">Collection öffnen</v-tooltip>
              </v-btn>
            </div>
          </template>
          <template v-slot:no-data>
            <div class="text-center text-medium-emphasis py-8">
              <v-icon size="48" class="mb-2 opacity-50">mdi-folder-open-outline</v-icon>
              <div>Noch keine Crawl-Jobs vorhanden</div>
            </div>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="4000" location="bottom right">
      {{ snackbar.text }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false">OK</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { io } from 'socket.io-client'

// Socket connection
let socket = null
const socketConnected = ref(false)
let reconnectAttempts = 0
const maxReconnectAttempts = 10

// Form data
const crawlForm = ref({
  urlsText: '',
  collectionName: '',
  description: '',
  maxPages: 50,
  maxDepth: 3
})

// State
const startingCrawl = ref(false)
const previewing = ref(false)
const preview = ref(null)
const jobs = ref([])
const loadingJobs = ref(false)
const urlError = ref(null)

// Live watching state
const watchingJob = ref(null)
const liveProgress = ref({})
const recentPages = ref([])

const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

// Job table headers
const jobHeaders = [
  { title: 'Status', key: 'status', width: '140px' },
  { title: 'URLs', key: 'urls', sortable: false },
  { title: 'Seiten', key: 'pages_crawled', width: '90px', align: 'center' },
  { title: 'Dokumente', key: 'documents_created', width: '100px', align: 'center' },
  { title: 'Gestartet', key: 'started_at', width: '160px' },
  { title: '', key: 'actions', width: '80px', sortable: false, align: 'end' }
]

// No polling - using WebSocket for real-time updates

// Computed
const urls = computed(() => {
  return crawlForm.value.urlsText
    .split('\n')
    .map(u => u.trim())
    .filter(u => u.length > 0)
})

const hasValidUrl = computed(() => {
  return urls.value.length > 0 && urls.value.every(u =>
    u.startsWith('http://') || u.startsWith('https://')
  )
})

const canStartCrawl = computed(() => {
  return hasValidUrl.value && crawlForm.value.collectionName?.trim() && !startingCrawl.value
})

const runningJobs = computed(() => {
  return jobs.value.filter(j => j.status === 'running' || j.status === 'queued')
})

const progressPercent = computed(() => {
  if (!liveProgress.value.max_pages) return 0
  return Math.min(100, Math.round((liveProgress.value.pages_crawled / liveProgress.value.max_pages) * 100))
})

// Validation
function validateUrls() {
  urlError.value = null
  if (crawlForm.value.urlsText.trim() && !hasValidUrl.value) {
    urlError.value = 'URLs müssen mit http:// oder https:// beginnen'
  }
}

// Socket Methods
function initSocket() {
  if (socket && socket.connected) return

  // Clean up old socket
  if (socket) {
    socket.disconnect()
    socket = null
  }

  const baseUrl = window.location.origin

  socket = io(baseUrl, {
    path: '/socket.io',
    transports: ['polling', 'websocket'], // Start with polling, upgrade to websocket
    reconnection: true,
    reconnectionAttempts: maxReconnectAttempts,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    timeout: 20000,
    forceNew: true
  })

  socket.on('connect', () => {
    console.log('[Crawler Socket] Connected:', socket.id)
    socketConnected.value = true
    reconnectAttempts = 0

    // Rejoin session if we were watching one
    if (watchingJob.value) {
      socket.emit('crawler:join_session', { session_id: watchingJob.value.job_id })
    }
  })

  socket.on('disconnect', (reason) => {
    console.log('[Crawler Socket] Disconnected:', reason)
    socketConnected.value = false
  })

  socket.on('connect_error', (error) => {
    console.warn('[Crawler Socket] Connection error:', error.message)
    reconnectAttempts++
    if (reconnectAttempts >= maxReconnectAttempts) {
      console.error('[Crawler Socket] Max reconnection attempts reached')
    }
  })

  socket.on('crawler:joined', (data) => {
    console.log('[Crawler Socket] Joined session:', data)
  })

  socket.on('crawler:progress', (data) => {
    console.log('[Crawler Socket] Progress:', data)
    updateProgress(data)
  })

  socket.on('crawler:page_crawled', (data) => {
    console.log('[Crawler Socket] Page crawled:', data)
    if (data.url) {
      recentPages.value.push(data)
      // Keep only last 50 pages
      if (recentPages.value.length > 50) {
        recentPages.value = recentPages.value.slice(-50)
      }
    }
  })

  socket.on('crawler:complete', (data) => {
    console.log('[Crawler Socket] Complete:', data)
    handleComplete(data)
  })

  socket.on('crawler:error', (data) => {
    console.error('[Crawler Socket] Error:', data)
    handleError(data)
  })

  socket.on('crawler:status', (data) => {
    console.log('[Crawler Socket] Status response:', data)
    if (data && watchingJob.value && watchingJob.value.job_id === data.session_id) {
      // Update liveProgress with all available fields from status
      liveProgress.value = {
        pages_crawled: data.pages_crawled || 0,
        max_pages: data.max_pages || liveProgress.value.max_pages || 50,
        current_url: data.current_url || null,
        current_url_index: data.current_url_index || 1,
        total_urls: data.urls?.length || liveProgress.value.total_urls || 1
      }
      // Also update watchingJob
      watchingJob.value = {
        ...watchingJob.value,
        pages_crawled: data.pages_crawled || 0,
        documents_created: data.documents_created || 0,
        status: data.status || watchingJob.value.status,
        errors: data.errors || watchingJob.value.errors
      }
    }
  })

  // Global job list updates (replaces polling)
  socket.on('crawler:jobs_list', (data) => {
    console.log('[Crawler Socket] Initial jobs list received:', data.jobs?.length || 0, 'jobs')
    if (data.jobs) {
      updateJobsList(data.jobs)
    }
  })

  socket.on('crawler:jobs_updated', (data) => {
    console.log('[Crawler Socket] Jobs updated:', data.jobs?.length || 0, 'jobs')
    if (data.jobs) {
      updateJobsList(data.jobs)
    }
  })
}

function updateJobsList(newJobs) {
  // Update jobs list from WebSocket
  for (const newJob of newJobs) {
    const existingIdx = jobs.value.findIndex(j => j.job_id === newJob.job_id)
    if (existingIdx !== -1) {
      // Update existing job
      Object.assign(jobs.value[existingIdx], newJob)
    } else {
      // Add new job
      jobs.value.push(newJob)
    }

    // Also update watchingJob and liveProgress if this is the watched job
    if (watchingJob.value && watchingJob.value.job_id === newJob.job_id) {
      watchingJob.value = { ...watchingJob.value, ...newJob }
      liveProgress.value = {
        pages_crawled: newJob.pages_crawled || 0,
        max_pages: newJob.max_pages || liveProgress.value.max_pages || 50,
        current_url: newJob.current_url || liveProgress.value.current_url,
        current_url_index: liveProgress.value.current_url_index || 1,
        total_urls: newJob.urls?.length || liveProgress.value.total_urls || 1
      }
    }
  }
  // Sort by start time descending
  jobs.value.sort((a, b) => {
    const dateA = new Date(b.started_at || b.queued_at || 0)
    const dateB = new Date(a.started_at || a.queued_at || 0)
    return dateA - dateB
  })
}

function subscribeToJobUpdates() {
  if (socket && socket.connected) {
    socket.emit('crawler:subscribe_jobs')
  } else if (socket) {
    socket.once('connect', () => {
      socket.emit('crawler:subscribe_jobs')
    })
  }
}

function updateProgress(data) {
  // Update live progress
  liveProgress.value = {
    pages_crawled: data.pages_crawled || 0,
    max_pages: data.max_pages || liveProgress.value.max_pages,
    current_url: data.current_url,
    current_url_index: data.current_url_index,
    total_urls: data.total_urls
  }

  // Update job in list
  const jobIndex = jobs.value.findIndex(j => j.job_id === data.session_id)
  if (jobIndex !== -1) {
    jobs.value[jobIndex].pages_crawled = data.pages_crawled
    jobs.value[jobIndex].status = data.status || jobs.value[jobIndex].status
    if (data.documents_created !== undefined) {
      jobs.value[jobIndex].documents_created = data.documents_created
    }
  }

  // Update watching job
  if (watchingJob.value && watchingJob.value.job_id === data.session_id) {
    watchingJob.value.pages_crawled = data.pages_crawled
    watchingJob.value.status = data.status || watchingJob.value.status
    if (data.documents_created !== undefined) {
      watchingJob.value.documents_created = data.documents_created
    }
  }
}

function handleComplete(data) {
  // Update job in list
  const jobIndex = jobs.value.findIndex(j => j.job_id === data.session_id)
  if (jobIndex !== -1) {
    jobs.value[jobIndex].status = 'completed'
    jobs.value[jobIndex].pages_crawled = data.pages_crawled
    jobs.value[jobIndex].documents_created = data.documents_created
    jobs.value[jobIndex].collection_id = data.collection_id
  }

  // Update watching job
  if (watchingJob.value && watchingJob.value.job_id === data.session_id) {
    watchingJob.value.status = 'completed'
    watchingJob.value.pages_crawled = data.pages_crawled
    watchingJob.value.documents_created = data.documents_created
    watchingJob.value.collection_id = data.collection_id
  }

  showSnackbar(`Crawl abgeschlossen: ${data.documents_created} Dokumente erstellt`, 'success')
}

function handleError(data) {
  // Update job in list
  const jobIndex = jobs.value.findIndex(j => j.job_id === data.session_id)
  if (jobIndex !== -1) {
    jobs.value[jobIndex].status = 'failed'
    jobs.value[jobIndex].error = data.error
  }

  // Update watching job
  if (watchingJob.value && watchingJob.value.job_id === data.session_id) {
    watchingJob.value.status = 'failed'
    watchingJob.value.error = data.error
  }

  showSnackbar(`Crawl-Fehler: ${data.error}`, 'error')
}

function watchJob(job) {
  initSocket()

  // Leave previous session
  if (watchingJob.value && watchingJob.value.job_id !== job.job_id && socket) {
    socket.emit('crawler:leave_session', { session_id: watchingJob.value.job_id })
  }

  watchingJob.value = { ...job }
  liveProgress.value = {
    pages_crawled: job.pages_crawled || 0,
    max_pages: job.max_pages || 50,  // Default to 50 if not available
    current_url: job.current_url || null,
    current_url_index: 1,
    total_urls: job.urls?.length || 1
  }
  recentPages.value = []

  // Join session and request status
  const joinSession = () => {
    if (socket) {
      socket.emit('crawler:join_session', { session_id: job.job_id })
      // Request current status to update liveProgress
      socket.emit('crawler:get_status', { session_id: job.job_id })
    }
  }

  // If socket is connected, join immediately
  if (socket && socket.connected) {
    joinSession()
  } else if (socket) {
    // Wait for connection then join
    socket.once('connect', joinSession)
  }
}

function stopWatching() {
  if (socket && watchingJob.value) {
    socket.emit('crawler:leave_session', { session_id: watchingJob.value.job_id })
  }
  watchingJob.value = null
  liveProgress.value = {}
  recentPages.value = []
}

// API Methods
async function previewUrl() {
  if (!urls.value.length) return

  previewing.value = true
  preview.value = null

  try {
    const response = await axios.post('/api/crawler/preview', {
      url: urls.value[0]
    })

    if (response.data.success) {
      preview.value = response.data.preview
    } else {
      showSnackbar(response.data.error || 'Vorschau fehlgeschlagen', 'error')
    }
  } catch (error) {
    console.error('Preview error:', error)
    showSnackbar(error.response?.data?.error || 'Fehler bei der Vorschau', 'error')
  } finally {
    previewing.value = false
  }
}

async function startBackgroundCrawl() {
  if (!canStartCrawl.value) return

  startingCrawl.value = true

  try {
    const response = await axios.post('/api/crawler/start', {
      urls: urls.value,
      collection_name: crawlForm.value.collectionName,
      collection_description: crawlForm.value.description,
      max_pages_per_site: crawlForm.value.maxPages,
      max_depth: crawlForm.value.maxDepth
    })

    if (response.data.success) {
      showSnackbar('Crawl gestartet - Live-Ansicht wird aktiviert', 'success')

      // Add job to list
      const newJob = {
        job_id: response.data.job_id,
        status: 'running',
        urls: response.data.urls,
        collection_name: response.data.collection_name,
        pages_crawled: 0,
        documents_created: 0,
        started_at: new Date().toISOString(),
        max_pages: crawlForm.value.maxPages * urls.value.length
      }
      jobs.value.unshift(newJob)

      // Auto-watch the new job
      watchJob(newJob)

      // Reset form
      crawlForm.value.urlsText = ''
      crawlForm.value.collectionName = ''
      crawlForm.value.description = ''
      preview.value = null
    } else {
      showSnackbar(response.data.error || 'Crawl konnte nicht gestartet werden', 'error')
    }
  } catch (error) {
    console.error('Start crawl error:', error)
    showSnackbar(error.response?.data?.error || 'Fehler beim Starten des Crawls', 'error')
  } finally {
    startingCrawl.value = false
  }
}

async function loadJobs() {
  loadingJobs.value = true
  try {
    const response = await axios.get('/api/crawler/jobs')
    if (response.data.success) {
      // Merge with existing jobs to preserve local state
      const newJobs = response.data.jobs || []
      for (const newJob of newJobs) {
        const existingIdx = jobs.value.findIndex(j => j.job_id === newJob.job_id)
        if (existingIdx !== -1) {
          // Update existing job
          Object.assign(jobs.value[existingIdx], newJob)
        } else {
          // Add new job
          jobs.value.push(newJob)
        }

        // Also update watchingJob and liveProgress if this is the watched job
        if (watchingJob.value && watchingJob.value.job_id === newJob.job_id) {
          // Update watchingJob with new data
          watchingJob.value = { ...watchingJob.value, ...newJob }

          // Update liveProgress
          liveProgress.value = {
            pages_crawled: newJob.pages_crawled || 0,
            max_pages: newJob.max_pages || liveProgress.value.max_pages || 50,
            current_url: newJob.current_url || liveProgress.value.current_url,
            current_url_index: liveProgress.value.current_url_index || 1,
            total_urls: newJob.urls?.length || liveProgress.value.total_urls || 1
          }
        }
      }
      // Sort by start time descending
      jobs.value.sort((a, b) => {
        const dateA = new Date(b.started_at || b.queued_at || 0)
        const dateB = new Date(a.started_at || a.queued_at || 0)
        return dateA - dateB
      })
    }
  } catch (error) {
    console.error('Error loading jobs:', error)
  } finally {
    loadingJobs.value = false
  }
}

function onJobClick(job) {
  if (job.status === 'running' || job.status === 'queued') {
    watchJob(job)
  }
}

// Helpers
function getStatusColor(status) {
  const colors = {
    completed: 'success',
    running: 'info',
    queued: 'warning',
    failed: 'error'
  }
  return colors[status] || 'grey'
}

function getStatusIcon(status) {
  const icons = {
    completed: 'mdi-check-circle',
    running: 'mdi-loading',
    queued: 'mdi-clock-outline',
    failed: 'mdi-alert-circle'
  }
  return icons[status] || 'mdi-clock'
}

function getStatusLabel(status) {
  const labels = {
    completed: 'Fertig',
    running: 'Läuft',
    queued: 'Wartend',
    failed: 'Fehler'
  }
  return labels[status] || status
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatNumber(num) {
  return num?.toLocaleString('de-DE') || '0'
}

function goToCollection(collectionId) {
  // TODO: Navigate to RAG section with collection filter
  showSnackbar(`Collection ${collectionId} erstellt - siehe RAG Dokumente`, 'info')
}

function showSnackbar(text, color = 'success') {
  snackbar.value = { show: true, text, color }
}

// Lifecycle
onMounted(() => {
  initSocket()
  // Subscribe to global job updates via WebSocket (replaces polling)
  subscribeToJobUpdates()
  // Also load jobs once via HTTP as fallback
  loadJobs()
})

onUnmounted(() => {
  if (socket) {
    // Unsubscribe from global job updates
    socket.emit('crawler:unsubscribe_jobs')
    if (watchingJob.value) {
      socket.emit('crawler:leave_session', { session_id: watchingJob.value.job_id })
    }
    socket.disconnect()
    socket = null
  }
})
</script>

<style scoped>
.live-session-card {
  border: 2px solid rgb(var(--v-theme-primary));
}

.activity-log {
  max-height: 250px;
  overflow-y: auto;
  font-family: 'Roboto Mono', monospace;
  font-size: 12px;
}

.log-entry {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.log-entry:last-child {
  border-bottom: none;
}

.log-url {
  color: rgba(255, 255, 255, 0.9);
}

.jobs-table :deep(tr) {
  cursor: pointer;
}

.jobs-table :deep(tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.ga-1 {
  gap: 4px;
}

.ga-2 {
  gap: 8px;
}
</style>
