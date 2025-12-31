<template>
  <div class="system-settings-section">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-cog</v-icon>
        System-Einstellungen
        <v-spacer />
        <LBtn
          v-if="hasChanges"
          variant="primary"
          :loading="saving"
          prepend-icon="mdi-content-save"
          @click="saveSettings"
        >
          Speichern
        </LBtn>
      </v-card-title>
      <v-card-subtitle>
        Konfigurierbare Parameter für Crawler, RAG und System-Verhalten
      </v-card-subtitle>

      <v-card-text>
        <v-skeleton-loader v-if="loading" type="article" />

        <template v-else>
          <!-- Crawler Timeouts -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-subtitle-1">
              <v-icon class="mr-2" size="small">mdi-timer-outline</v-icon>
              Crawler Timeouts
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.crawl_timeout_seconds"
                    label="Crawl Timeout (Sekunden)"
                    type="number"
                    :min="60"
                    :max="86400"
                    variant="outlined"
                    density="comfortable"
                    hint="Standard: 3600 (1 Stunde). Für große Websites erhöhen."
                    persistent-hint
                  >
                    <template #append-inner>
                      <span class="text-caption text-medium-emphasis">
                        {{ formatDuration(settings.crawl_timeout_seconds) }}
                      </span>
                    </template>
                  </v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.embedding_timeout_seconds"
                    label="Embedding Timeout (Sekunden)"
                    type="number"
                    :min="60"
                    :max="86400"
                    variant="outlined"
                    density="comfortable"
                    hint="Standard: 7200 (2 Stunden). Für große Collections erhöhen."
                    persistent-hint
                  >
                    <template #append-inner>
                      <span class="text-caption text-medium-emphasis">
                        {{ formatDuration(settings.embedding_timeout_seconds) }}
                      </span>
                    </template>
                  </v-text-field>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- Crawler Defaults -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-subtitle-1">
              <v-icon class="mr-2" size="small">mdi-spider-web</v-icon>
              Crawler Defaults
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.crawler_default_max_pages"
                    label="Standard Max-Seiten"
                    type="number"
                    :min="1"
                    :max="10000"
                    variant="outlined"
                    density="comfortable"
                    hint="Standard: 500. Maximale Seiten pro Crawl im Chatbot Wizard."
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.crawler_default_max_depth"
                    label="Standard Crawl-Tiefe"
                    type="number"
                    :min="1"
                    :max="10"
                    variant="outlined"
                    density="comfortable"
                    hint="Standard: 3. Wie viele Link-Ebenen verfolgt werden."
                    persistent-hint
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- RAG Settings -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-subtitle-1">
              <v-icon class="mr-2" size="small">mdi-file-document-multiple</v-icon>
              RAG Chunking
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.rag_default_chunk_size"
                    label="Standard Chunk-Größe"
                    type="number"
                    :min="100"
                    :max="10000"
                    variant="outlined"
                    density="comfortable"
                    hint="Standard: 1000 Zeichen pro Chunk."
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.rag_default_chunk_overlap"
                    label="Standard Chunk-Überlappung"
                    type="number"
                    :min="0"
                    :max="5000"
                    variant="outlined"
                    density="comfortable"
                    hint="Standard: 200 Zeichen Überlappung zwischen Chunks."
                    persistent-hint
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- Zotero OAuth Settings -->
          <v-card variant="outlined">
            <v-card-title class="text-subtitle-1 d-flex align-center">
              <v-icon class="mr-2" size="small">mdi-book-open-page-variant</v-icon>
              Zotero Integration
              <v-spacer />
              <v-chip
                :color="zoteroStatus.oauth_available ? 'success' : 'warning'"
                variant="tonal"
                size="small"
              >
                <v-icon start size="small">
                  {{ zoteroStatus.oauth_available ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                </v-icon>
                {{ zoteroStatusLabel }}
              </v-chip>
            </v-card-title>
            <v-card-text>
              <!-- Info Alert -->
              <v-alert
                type="info"
                variant="tonal"
                density="compact"
                class="mb-4"
              >
                <div class="text-body-2">
                  Zotero OAuth ermöglicht Usern, ihre Bibliotheken mit LaTeX-Workspaces zu synchronisieren.
                  Registriere eine App unter
                  <a href="https://www.zotero.org/oauth/apps" target="_blank" rel="noopener">
                    zotero.org/oauth/apps
                  </a>.
                  <br>
                  <strong>Priorität:</strong> .env-Variablen → Datenbank-Fallback
                </div>
              </v-alert>

              <!-- Environment Variables Status (read-only) -->
              <div class="mb-4">
                <div class="text-subtitle-2 mb-2 d-flex align-center">
                  <v-icon size="small" class="mr-1">mdi-file-cog</v-icon>
                  Umgebungsvariablen (.env)
                  <v-chip
                    v-if="zoteroStatus.active_source === 'env'"
                    color="primary"
                    variant="flat"
                    size="x-small"
                    class="ml-2"
                  >
                    AKTIV
                  </v-chip>
                </div>
                <v-row>
                  <v-col cols="12" md="6">
                    <v-text-field
                      :model-value="zoteroStatus.env?.client_key || '(nicht gesetzt)'"
                      label="ZOTERO_CLIENT_KEY"
                      variant="outlined"
                      density="compact"
                      readonly
                      disabled
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      :model-value="zoteroStatus.env?.client_secret_set ? '••••••••' : '(nicht gesetzt)'"
                      label="ZOTERO_CLIENT_SECRET"
                      variant="outlined"
                      density="compact"
                      readonly
                      disabled
                    />
                  </v-col>
                </v-row>
              </div>

              <v-divider class="mb-4" />

              <!-- Database Fallback (editable) -->
              <div>
                <div class="text-subtitle-2 mb-2 d-flex align-center">
                  <v-icon size="small" class="mr-1">mdi-database</v-icon>
                  Datenbank-Fallback
                  <v-chip
                    v-if="zoteroStatus.active_source === 'database'"
                    color="primary"
                    variant="flat"
                    size="x-small"
                    class="ml-2"
                  >
                    AKTIV
                  </v-chip>
                  <v-spacer />
                  <LBtn
                    v-if="zoteroDbHasChanges"
                    variant="primary"
                    size="small"
                    :loading="savingZotero"
                    prepend-icon="mdi-content-save"
                    @click="saveZoteroSettings"
                  >
                    Speichern
                  </LBtn>
                </div>

                <v-switch
                  v-model="zoteroDb.enabled"
                  label="Datenbank-Fallback aktivieren"
                  color="primary"
                  hide-details
                  density="compact"
                  class="mb-3"
                  :disabled="zoteroStatus.env?.configured"
                />

                <v-row>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="zoteroDb.client_key"
                      label="Client Key"
                      variant="outlined"
                      density="comfortable"
                      hint="Von zotero.org/oauth/apps"
                      persistent-hint
                      :disabled="!zoteroDb.enabled || zoteroStatus.env?.configured"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="zoteroDb.client_secret"
                      :label="zoteroStatus.database?.client_secret_set ? 'Client Secret (gesetzt)' : 'Client Secret'"
                      :type="showSecret ? 'text' : 'password'"
                      variant="outlined"
                      density="comfortable"
                      :placeholder="zoteroStatus.database?.client_secret_set ? '••••••••' : ''"
                      hint="Leer lassen um bestehendes Secret beizubehalten"
                      persistent-hint
                      :disabled="!zoteroDb.enabled || zoteroStatus.env?.configured"
                    >
                      <template #append-inner>
                        <v-btn
                          icon
                          variant="text"
                          size="small"
                          @click="showSecret = !showSecret"
                        >
                          <v-icon>{{ showSecret ? 'mdi-eye-off' : 'mdi-eye' }}</v-icon>
                        </v-btn>
                      </template>
                    </v-text-field>
                  </v-col>
                </v-row>

                <v-alert
                  v-if="zoteroStatus.env?.configured"
                  type="info"
                  variant="tonal"
                  density="compact"
                  class="mt-3"
                >
                  .env-Variablen sind gesetzt und haben Priorität. Datenbank-Einstellungen werden ignoriert.
                </v-alert>
              </div>
            </v-card-text>
          </v-card>

          <!-- Last Updated Info -->
          <div v-if="settings.updated_at" class="text-caption text-medium-emphasis mt-4">
            Zuletzt aktualisiert: {{ formatDate(settings.updated_at) }}
          </div>
        </template>
      </v-card-text>
    </v-card>

    <!-- Snackbar for feedback -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'

const loading = ref(true)
const saving = ref(false)
const savingZotero = ref(false)
const showSecret = ref(false)

const snackbar = reactive({
  show: false,
  text: '',
  color: 'success'
})

const settings = reactive({
  crawl_timeout_seconds: 3600,
  embedding_timeout_seconds: 7200,
  crawler_default_max_pages: 500,
  crawler_default_max_depth: 3,
  rag_default_chunk_size: 1000,
  rag_default_chunk_overlap: 200,
  updated_at: null
})

const originalSettings = ref({})

// Zotero OAuth state
const zoteroStatus = reactive({
  env: { configured: false, client_key: null, client_secret_set: false },
  database: { enabled: false, configured: false, client_key: '', client_secret_set: false },
  active_source: 'none',
  oauth_available: false
})

const zoteroDb = reactive({
  enabled: false,
  client_key: '',
  client_secret: ''
})

const originalZoteroDb = ref({})

const hasChanges = computed(() => {
  return JSON.stringify(settings) !== JSON.stringify(originalSettings.value)
})

const zoteroDbHasChanges = computed(() => {
  const current = {
    enabled: zoteroDb.enabled,
    client_key: zoteroDb.client_key,
    client_secret: zoteroDb.client_secret
  }
  const original = {
    enabled: originalZoteroDb.value.enabled,
    client_key: originalZoteroDb.value.client_key,
    client_secret: ''
  }
  return JSON.stringify(current) !== JSON.stringify(original)
})

const zoteroStatusLabel = computed(() => {
  if (zoteroStatus.active_source === 'env') return 'Aktiv (.env)'
  if (zoteroStatus.active_source === 'database') return 'Aktiv (DB)'
  return 'Nicht konfiguriert'
})

async function loadSettings() {
  loading.value = true
  try {
    // Load both settings in parallel
    const [settingsRes, zoteroRes] = await Promise.all([
      axios.get('/api/admin/system/settings'),
      axios.get('/api/admin/system/zotero-oauth').catch(() => ({ data: { success: false } }))
    ])

    if (settingsRes.data.success) {
      Object.assign(settings, settingsRes.data.settings)
      originalSettings.value = { ...settingsRes.data.settings }
    }

    if (zoteroRes.data.success) {
      const z = zoteroRes.data.zotero_oauth
      Object.assign(zoteroStatus, z)

      // Set editable database fields
      zoteroDb.enabled = z.database?.enabled || false
      zoteroDb.client_key = z.database?.client_key || ''
      zoteroDb.client_secret = ''
      originalZoteroDb.value = {
        enabled: z.database?.enabled || false,
        client_key: z.database?.client_key || ''
      }
    }
  } catch (error) {
    console.error('Failed to load system settings:', error)
    snackbar.text = 'Fehler beim Laden der Einstellungen'
    snackbar.color = 'error'
    snackbar.show = true
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  try {
    const response = await axios.patch('/api/admin/system/settings', {
      crawl_timeout_seconds: settings.crawl_timeout_seconds,
      embedding_timeout_seconds: settings.embedding_timeout_seconds,
      crawler_default_max_pages: settings.crawler_default_max_pages,
      crawler_default_max_depth: settings.crawler_default_max_depth,
      rag_default_chunk_size: settings.rag_default_chunk_size,
      rag_default_chunk_overlap: settings.rag_default_chunk_overlap
    })

    if (response.data.success) {
      Object.assign(settings, response.data.settings)
      originalSettings.value = { ...response.data.settings }
      snackbar.text = 'Einstellungen gespeichert'
      snackbar.color = 'success'
      snackbar.show = true
    }
  } catch (error) {
    console.error('Failed to save system settings:', error)
    snackbar.text = 'Fehler beim Speichern'
    snackbar.color = 'error'
    snackbar.show = true
  } finally {
    saving.value = false
  }
}

async function saveZoteroSettings() {
  savingZotero.value = true
  try {
    const payload = {
      enabled: zoteroDb.enabled,
      client_key: zoteroDb.client_key
    }
    // Only send client_secret if user entered a new one
    if (zoteroDb.client_secret) {
      payload.client_secret = zoteroDb.client_secret
    }

    const response = await axios.patch('/api/admin/system/zotero-oauth', payload)

    if (response.data.success) {
      const z = response.data.zotero_oauth
      Object.assign(zoteroStatus, z)

      // Reset editable fields
      zoteroDb.enabled = z.database?.enabled || false
      zoteroDb.client_key = z.database?.client_key || ''
      zoteroDb.client_secret = ''
      originalZoteroDb.value = {
        enabled: z.database?.enabled || false,
        client_key: z.database?.client_key || ''
      }

      snackbar.text = 'Zotero-Einstellungen gespeichert'
      snackbar.color = 'success'
      snackbar.show = true
    }
  } catch (error) {
    console.error('Failed to save Zotero OAuth settings:', error)
    snackbar.text = 'Fehler beim Speichern der Zotero-Einstellungen'
    snackbar.color = 'error'
    snackbar.show = true
  } finally {
    savingZotero.value = false
  }
}

function formatDuration(seconds) {
  if (!seconds) return ''
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0 && minutes > 0) return `${hours}h ${minutes}min`
  if (hours > 0) return `${hours}h`
  return `${minutes}min`
}

function formatDate(dateString) {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('de-DE')
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.system-settings-section {
  max-width: 900px;
}
</style>
