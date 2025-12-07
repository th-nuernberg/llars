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
            :color="socketConnected ? 'success' : isReconnecting ? 'warning' : 'error'"
            :variant="socketConnected ? 'flat' : 'outlined'"
            size="small"
            class="font-weight-medium"
          >
            <v-progress-circular v-if="isReconnecting" indeterminate size="12" width="2" class="mr-1" />
            <v-icon v-else start size="14">{{ socketConnected ? 'mdi-wifi' : 'mdi-wifi-off' }}</v-icon>
            {{ socketConnected ? 'Live verbunden' : isReconnecting ? 'Verbinde...' : 'Offline' }}
          </v-chip>
          <LIconBtn
            icon="mdi-refresh"
            :loading="loadingJobs"
            @click="loadJobs"
          />
        </div>
      </v-card-text>
    </v-card>

    <!-- Reconnection Alert -->
    <v-slide-y-transition>
      <v-alert
        v-if="isReconnecting"
        type="warning"
        variant="tonal"
        class="mb-4"
        density="compact"
      >
        <template v-slot:prepend>
          <v-progress-circular indeterminate size="20" width="2" color="warning" />
        </template>
        <span class="font-weight-medium">Verbindung wird wiederhergestellt...</span>
        <span class="text-body-2 ml-2">Live-Updates werden fortgesetzt, sobald die Verbindung steht.</span>
      </v-alert>
    </v-slide-y-transition>

    <!-- Reconnection Failed Alert -->
    <v-slide-y-transition>
      <v-alert
        v-if="reconnectionFailed"
        type="error"
        variant="tonal"
        class="mb-4"
        density="compact"
        closable
        @click:close="reconnectionFailed = false"
      >
        <template v-slot:prepend>
          <v-icon>mdi-wifi-off</v-icon>
        </template>
        <div class="d-flex justify-space-between align-center flex-wrap ga-2">
          <div>
            <span class="font-weight-medium">Verbindung fehlgeschlagen</span>
            <span class="text-body-2 ml-2">Live-Updates sind nicht verfügbar.</span>
          </div>
          <LBtn
            variant="text"
            size="small"
            @click="retryConnection"
            prepend-icon="mdi-refresh"
          >
            Erneut versuchen
          </LBtn>
        </div>
      </v-alert>
    </v-slide-y-transition>

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
          <LBtn
            variant="primary"
            size="small"
            @click="watchJob(runningJobs[0])"
            prepend-icon="mdi-eye"
          >
            Live ansehen
          </LBtn>
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
              :hint="!crawlForm.collectionName?.trim() ? 'Name ist erforderlich' : ''"
              :persistent-hint="!crawlForm.collectionName?.trim()"
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
                  <!-- Collection Mode Selection -->
                  <div class="mb-4">
                    <div class="text-caption text-medium-emphasis mb-2">Collection-Modus</div>
                    <v-radio-group v-model="crawlForm.collectionMode" density="compact" hide-details class="mb-3">
                      <v-radio value="new" label="Neue Collection erstellen" />
                      <v-radio value="existing" label="Zu bestehender Collection hinzufügen" />
                    </v-radio-group>

                    <!-- Existing Collection Dropdown -->
                    <v-autocomplete
                      v-if="crawlForm.collectionMode === 'existing'"
                      v-model="crawlForm.existingCollectionId"
                      :items="collections"
                      item-title="display_name"
                      item-value="id"
                      label="Collection auswählen"
                      variant="outlined"
                      density="compact"
                      :loading="loadingCollections"
                      prepend-inner-icon="mdi-folder-multiple"
                      clearable
                      class="mb-2"
                    >
                      <template v-slot:item="{ props, item }">
                        <v-list-item v-bind="props">
                          <template v-slot:append>
                            <v-chip size="x-small" color="primary" variant="tonal">
                              {{ item.raw.document_count }} Docs
                            </v-chip>
                          </template>
                        </v-list-item>
                      </template>
                      <template v-slot:no-data>
                        <v-list-item>
                          <v-list-item-title class="text-body-2 text-medium-emphasis">
                            Keine Collections gefunden
                          </v-list-item-title>
                        </v-list-item>
                      </template>
                    </v-autocomplete>

                    <v-alert
                      v-if="crawlForm.collectionMode === 'existing'"
                      type="info"
                      variant="tonal"
                      density="compact"
                      class="text-caption"
                    >
                      <strong>Verlinken statt Duplizieren:</strong> Seiten mit identischem Inhalt werden nur verlinkt, nicht erneut gespeichert.
                    </v-alert>
                  </div>

                  <v-divider class="mb-4" />

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
              <LBtn
                variant="primary"
                :loading="startingCrawl"
                :disabled="!canStartCrawl"
                @click="startBackgroundCrawl"
                prepend-icon="mdi-spider-web"
              >
                Crawl starten
              </LBtn>
              <LBtn
                variant="secondary"
                :loading="previewing"
                :disabled="!hasValidUrl"
                @click="previewUrl"
                prepend-icon="mdi-magnify"
              >
                Vorschau
              </LBtn>
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
            <LIconBtn
              icon="mdi-close"
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
                <v-tooltip location="bottom">
                  <template #activator="{ props }">
                    <v-card v-bind="props" variant="tonal" color="info" class="text-center pa-3">
                      <div class="text-h5 font-weight-bold">{{ watchingJob.documents_linked || 0 }}</div>
                      <div class="text-caption">Verlinkt</div>
                    </v-card>
                  </template>
                  <div v-if="(watchingJob.documents_linked || 0) > 0">
                    <div>{{ watchingJob.documents_linked }} bereits existierende Dokumente zur Collection verlinkt</div>
                  </div>
                  <span v-else>Keine existierenden Dokumente verlinkt</span>
                </v-tooltip>
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
              :type="watchingJob.documents_created > 0 ? 'success' : 'warning'"
              variant="tonal"
              class="mt-4"
            >
              <div class="d-flex justify-space-between align-center">
                <div>
                  <strong>Crawl erfolgreich abgeschlossen!</strong>
                  <div class="text-body-2">{{ watchingJob.documents_created }} Dokumente wurden erstellt.</div>
                  <div v-if="watchingJob.skipped_existing > 0" class="text-body-2 text-warning">
                    <v-icon size="small" color="warning" class="mr-1">mdi-alert-circle</v-icon>
                    {{ watchingJob.skipped_existing }} Seite(n) übersprungen (Inhalt bereits in der Datenbank vorhanden).
                  </div>
                </div>
                <LBtn
                  v-if="watchingJob.collection_id"
                  variant="success"
                  size="small"
                  @click="goToCollection(watchingJob.collection_id)"
                  prepend-icon="mdi-folder-open"
                >
                  Zur Collection
                </LBtn>
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
            <LBtn
              v-if="runningJobs.length > 0"
              variant="primary"
              @click="watchJob(runningJobs[0])"
              prepend-icon="mdi-eye"
            >
              Laufenden Crawl ansehen
            </LBtn>
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
        <LIconBtn
          icon="mdi-refresh"
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
              <LIconBtn
                v-if="item.status === 'running' || item.status === 'queued'"
                icon="mdi-eye"
                variant="primary"
                tooltip="Live ansehen"
                size="x-small"
                @click.stop="watchJob(item)"
              />
              <LIconBtn
                v-if="item.collection_id"
                icon="mdi-folder-open"
                variant="success"
                tooltip="Collection öffnen"
                size="x-small"
                @click.stop="goToCollection(item.collection_id)"
              />
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
        <LBtn variant="text" @click="snackbar.show = false">OK</LBtn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import {
  useCrawlerSocket,
  useCrawlerJobs,
  useCrawlerForm,
  useCrawlerHelpers
} from './WebCrawlerTool/composables'

// Initialize composables
const {
  snackbar,
  jobHeaders,
  getStatusColor,
  getStatusIcon,
  getStatusLabel,
  formatDate,
  formatNumber,
  showSnackbar,
  goToCollection
} = useCrawlerHelpers()

const {
  jobs,
  loadingJobs,
  watchingJob,
  liveProgress,
  recentPages,
  runningJobs,
  progressPercent,
  loadJobs,
  updateJobsList,
  watchJob: watchJobBase,
  stopWatching: stopWatchingBase,
  updateProgress,
  addRecentPage,
  handleComplete: handleCompleteBase,
  handleError: handleErrorBase,
  handleStatus
} = useCrawlerJobs()

const {
  crawlForm,
  collections,
  loadingCollections,
  startingCrawl,
  previewing,
  preview,
  urlError,
  urls,
  hasValidUrl,
  canStartCrawl,
  validateUrls,
  loadCollections,
  previewUrl: previewUrlBase,
  startBackgroundCrawl: startBackgroundCrawlBase,
  resetForm
} = useCrawlerForm()

// Socket with callbacks
const socketCallbacks = {
  onConnect: () => {
    // Rejoin session if we were watching one
    if (watchingJob.value) {
      joinSession(watchingJob.value.job_id)
    }
  },
  onProgress: (data) => {
    updateProgress(data)
  },
  onPageCrawled: (data) => {
    addRecentPage(data)
  },
  onComplete: (data) => {
    const result = handleCompleteBase(data)
    // Show appropriate snackbar message
    if (result.documents_created > 0) {
      showSnackbar(`Crawl abgeschlossen: ${result.documents_created} Dokumente erstellt`, 'success')
    } else if (result.skipped_existing > 0) {
      showSnackbar(`Crawl abgeschlossen: Alle ${result.skipped_existing} Seiten waren bereits in der Datenbank vorhanden`, 'warning')
    } else {
      showSnackbar('Crawl abgeschlossen: Keine neuen Dokumente erstellt', 'info')
    }
  },
  onError: (data) => {
    handleErrorBase(data)
    showSnackbar(`Crawl-Fehler: ${data.error}`, 'error')
  },
  onStatus: (data) => {
    handleStatus(data)
  },
  onJobsList: (jobsList) => {
    updateJobsList(jobsList)
  },
  onJobsUpdated: (jobsList) => {
    updateJobsList(jobsList)
  }
}

const {
  socketConnected,
  isReconnecting,
  reconnectionFailed,
  initSocket,
  subscribeToJobUpdates,
  joinSession,
  leaveSession,
  retryConnection: retryConnectionBase,
  disconnect,
  getSocket
} = useCrawlerSocket(socketCallbacks)

// Wrapped methods that integrate socket and jobs
function watchJob(job) {
  initSocket()

  // Leave previous session
  if (watchingJob.value && watchingJob.value.job_id !== job.job_id) {
    leaveSession(watchingJob.value.job_id)
  }

  watchJobBase(job)

  // Join session and request status
  const socket = getSocket()
  if (socket && socket.connected) {
    joinSession(job.job_id)
  }
}

function stopWatching() {
  if (watchingJob.value) {
    leaveSession(watchingJob.value.job_id)
  }
  stopWatchingBase()
}

async function previewUrl() {
  try {
    await previewUrlBase()
  } catch (error) {
    showSnackbar(error.response?.data?.error || error.message || 'Fehler bei der Vorschau', 'error')
  }
}

async function startBackgroundCrawl() {
  try {
    const newJob = await startBackgroundCrawlBase()
    if (newJob) {
      showSnackbar('Crawl gestartet - Live-Ansicht wird aktiviert', 'success')

      // Check if job already exists in list (from WebSocket update)
      const existingIdx = jobs.value.findIndex(j => j.job_id === newJob.job_id)
      if (existingIdx === -1) {
        jobs.value.unshift(newJob)
      }

      // Auto-watch the new job
      watchJob(newJob)

      // Reset form
      setTimeout(() => {
        resetForm()
      }, 100)
    }
  } catch (error) {
    showSnackbar(error.response?.data?.error || error.message || 'Fehler beim Starten des Crawls', 'error')
  }
}

function retryConnection() {
  retryConnectionBase()
}

function onJobClick(job) {
  if (job.status === 'running' || job.status === 'queued') {
    watchJob(job)
  }
}

// Lifecycle
onMounted(() => {
  initSocket()
  subscribeToJobUpdates()
  loadJobs()
  loadCollections().catch(error => {
    showSnackbar('Fehler beim Laden der Collections', 'error')
  })
})

onUnmounted(() => {
  disconnect()
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
