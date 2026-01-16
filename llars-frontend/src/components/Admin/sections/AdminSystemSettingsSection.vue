<template>
  <div class="system-settings-section">
    <v-card>
      <v-card-title class="d-flex align-center">
        <LIcon class="mr-2">mdi-cog</LIcon>
        System-Einstellungen
      </v-card-title>
      <v-card-subtitle>
        Konfigurierbare Parameter für Crawler, RAG und System-Verhalten. Änderungen werden automatisch gespeichert.
      </v-card-subtitle>

      <v-card-text>
        <v-skeleton-loader v-if="loading" type="article" />

        <template v-else>
          <!-- Crawler Timeouts -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-subtitle-1 d-flex align-center">
              <LIcon class="mr-2" size="small">mdi-timer-outline</LIcon>
              Crawler Timeouts
              <v-spacer />
              <LStatusChip :state="sectionStates.crawler" />
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
            <v-card-title class="text-subtitle-1 d-flex align-center">
              <LIcon class="mr-2" size="small">mdi-spider-web</LIcon>
              Crawler Defaults
              <v-spacer />
              <LStatusChip :state="sectionStates.crawlerDefaults" />
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
            <v-card-title class="text-subtitle-1 d-flex align-center">
              <LIcon class="mr-2" size="small">mdi-file-document-multiple</LIcon>
              RAG Chunking
              <v-spacer />
              <LStatusChip :state="sectionStates.rag" />
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

          <!-- LLM Logging Settings -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-subtitle-1 d-flex align-center">
              <LIcon class="mr-2" size="small">mdi-robot-outline</LIcon>
              LLM Logging
              <v-spacer />
              <LStatusChip :state="sectionStates.llmLogging" />
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" md="6">
                  <v-switch
                    v-model="settings.llm_ai_log_responses"
                    label="Antworten loggen"
                    color="primary"
                    hide-details
                    density="compact"
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-switch
                    v-model="settings.llm_ai_log_prompts"
                    label="Prompts loggen"
                    color="warning"
                    hide-details
                    density="compact"
                  />
                </v-col>
              </v-row>

              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="settings.llm_ai_log_tasks"
                    label="Tasks (Komma-getrennt)"
                    variant="outlined"
                    density="comfortable"
                    hint="z.B. authenticity, ranking, rating – leer = alle"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.llm_ai_log_response_max"
                    label="Max Zeichen (Antworten)"
                    type="number"
                    :min="0"
                    :max="10000"
                    variant="outlined"
                    density="comfortable"
                    hint="Standard: 800"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.llm_ai_log_prompt_max"
                    label="Max Zeichen (Prompts)"
                    type="number"
                    :min="0"
                    :max="10000"
                    variant="outlined"
                    density="comfortable"
                    hint="Standard: 800"
                    persistent-hint
                  />
                </v-col>
              </v-row>

              <v-alert
                v-if="settings.llm_ai_log_prompts"
                type="warning"
                variant="tonal"
                density="compact"
                class="mt-2"
              >
                Prompt-Logging enthält Konversationen. Bitte datenschutzkonform verwenden.
              </v-alert>
            </v-card-text>
          </v-card>

          <!-- Referral System Settings -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-subtitle-1 d-flex align-center">
              <LIcon class="mr-2" size="small">mdi-account-multiple-plus</LIcon>
              Referral-System
              <v-spacer />
              <LStatusChip :state="sectionStates.referral" />
            </v-card-title>
            <v-card-text>
              <v-alert
                type="info"
                variant="tonal"
                density="compact"
                class="mb-4"
              >
                Das Referral-System ermöglicht die Selbst-Registrierung über Einladungslinks.
                Verwalte Kampagnen und Links im <strong>Referrals</strong>-Tab.
              </v-alert>

              <v-row>
                <v-col cols="12" md="6">
                  <v-switch
                    v-model="settings.referral_system_enabled"
                    label="Referral-System aktivieren"
                    color="primary"
                    hide-details
                    density="compact"
                    class="mb-2"
                  />
                  <div class="text-caption text-medium-emphasis ml-10">
                    Aktiviert die Verwaltung von Referral-Kampagnen und Links.
                  </div>
                </v-col>
                <v-col cols="12" md="6">
                  <v-switch
                    v-model="settings.self_registration_enabled"
                    label="Selbst-Registrierung aktivieren"
                    color="success"
                    hide-details
                    density="compact"
                    class="mb-2"
                    :disabled="!settings.referral_system_enabled"
                  />
                  <div class="text-caption text-medium-emphasis ml-10">
                    Zeigt den "Registrieren"-Button an und erlaubt die Registrierung über gültige Referral-Links.
                  </div>
                </v-col>
              </v-row>

              <v-row class="mt-2">
                <v-col cols="12" md="6">
                  <v-select
                    v-model="settings.default_referral_role"
                    :items="availableRoles"
                    item-title="label"
                    item-value="value"
                    label="Standard-Rolle für neue Benutzer"
                    variant="outlined"
                    density="comfortable"
                    hint="Rolle, die neuen Benutzern bei der Registrierung zugewiesen wird (falls kein Link-spezifischer Override)."
                    persistent-hint
                    :disabled="!settings.referral_system_enabled"
                  />
                </v-col>
              </v-row>

              <v-alert
                v-if="settings.self_registration_enabled"
                type="success"
                variant="tonal"
                density="compact"
                class="mt-4"
              >
                <LIcon start size="small">mdi-check-circle</LIcon>
                Selbst-Registrierung ist aktiv. Der "Registrieren"-Button wird auf der Login-Seite angezeigt.
              </v-alert>
            </v-card-text>
          </v-card>

          <!-- AI Assistant Settings -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-subtitle-1 d-flex align-center">
              <LIcon class="mr-2" size="small">mdi-robot</LIcon>
              KI-Assistent (LaTeX Collab)
              <v-spacer />
              <LStatusChip :state="sectionStates.aiAssistant" />
            </v-card-title>
            <v-card-text>
              <v-alert
                type="info"
                variant="tonal"
                density="compact"
                class="mb-4"
              >
                Der KI-Assistent kann in LaTeX Collab Kommentare automatisch auflösen.
                Die KI-Farbe ist exklusiv für den Assistenten reserviert und kann nicht von Nutzern gewählt werden.
              </v-alert>

              <v-row>
                <v-col cols="12" md="6">
                  <v-switch
                    v-model="settings.ai_assistant_enabled"
                    label="KI-Assistent aktivieren"
                    color="primary"
                    hide-details
                    density="compact"
                    class="mb-2"
                  />
                  <div class="text-caption text-medium-emphasis ml-10">
                    Aktiviert den KI-Button bei Kommentaren für automatische Auflösung.
                  </div>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="settings.ai_assistant_username"
                    label="KI-Anzeigename"
                    variant="outlined"
                    density="comfortable"
                    hint="Name, der als Autor bei KI-Antworten angezeigt wird."
                    persistent-hint
                    maxlength="50"
                  />
                </v-col>
              </v-row>

              <v-row class="mt-2">
                <v-col cols="12" md="6">
                  <div class="d-flex align-center">
                    <v-menu
                      :close-on-content-click="false"
                      location="bottom start"
                    >
                      <template #activator="{ props }">
                        <div
                          v-bind="props"
                          class="color-preview cursor-pointer mr-3"
                          :style="{ backgroundColor: settings.ai_assistant_color }"
                        />
                      </template>
                      <v-color-picker
                        v-model="settings.ai_assistant_color"
                        mode="hex"
                        :modes="['hex']"
                        hide-inputs
                        show-swatches
                        :swatches="aiColorSwatches"
                      />
                    </v-menu>
                    <v-text-field
                      v-model="settings.ai_assistant_color"
                      label="KI-Farbe (Hex)"
                      variant="outlined"
                      density="comfortable"
                      hint="Reservierte Farbe für KI-Änderungen. Standard: #9B59B6 (Lila)"
                      persistent-hint
                      maxlength="7"
                      style="max-width: 200px;"
                    />
                  </div>
                </v-col>
                <v-col cols="12" md="6" class="d-flex align-center">
                  <div class="ai-preview-card pa-3 rounded">
                    <div class="text-caption text-medium-emphasis mb-1">Vorschau:</div>
                    <div class="d-flex align-center">
                      <div
                        class="ai-avatar mr-2"
                        :style="{ backgroundColor: settings.ai_assistant_color }"
                      >
                        <LIcon size="small" color="white">mdi-robot</LIcon>
                      </div>
                      <span class="font-weight-medium">{{ settings.ai_assistant_username || 'LLARS KI' }}</span>
                    </div>
                  </div>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- Zotero OAuth Settings -->
          <v-card variant="outlined">
            <v-card-title class="text-subtitle-1 d-flex align-center">
              <LIcon class="mr-2" size="small">zotero</LIcon>
              Zotero Integration
              <v-spacer />
              <v-chip
                :color="zoteroStatus.oauth_available ? 'success' : 'warning'"
                variant="tonal"
                size="x-small"
              >
                <LIcon start size="x-small">
                  {{ zoteroStatus.oauth_available ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                </LIcon>
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
                  <LIcon size="small" class="mr-1">mdi-file-cog</LIcon>
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
                  <LIcon size="small" class="mr-1">mdi-database</LIcon>
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
                  <LStatusChip :state="sectionStates.zotero" />
                </div>
                <v-row>
                  <v-col cols="12">
                    <v-switch
                      v-model="zoteroDb.enabled"
                      label="Datenbank-Fallback aktivieren"
                      color="primary"
                      hide-details
                      density="compact"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="zoteroDb.client_key"
                      label="Client Key"
                      variant="outlined"
                      density="compact"
                      :disabled="!zoteroDb.enabled"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="zoteroDb.client_secret"
                      :type="showSecret ? 'text' : 'password'"
                      label="Client Secret (leer = unverändert)"
                      variant="outlined"
                      density="compact"
                      :disabled="!zoteroDb.enabled"
                      placeholder="Neues Secret eingeben..."
                    >
                      <template #append-inner>
                        <v-btn
                          :icon="showSecret ? 'mdi-eye-off' : 'mdi-eye'"
                          variant="text"
                          density="compact"
                          size="small"
                          @click="showSecret = !showSecret"
                        />
                      </template>
                    </v-text-field>
                  </v-col>
                </v-row>
              </div>
            </v-card-text>
          </v-card>

          <!-- Last updated info -->
          <div v-if="settings.updated_at" class="text-caption text-medium-emphasis mt-4">
            Zuletzt aktualisiert: {{ formatDate(settings.updated_at) }}
          </div>
        </template>
      </v-card-text>
    </v-card>

    <!-- Snackbar for errors only -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { logI18n, logI18nParams } from '@/utils/logI18n'
import { useReferralSystem } from '@/composables/useReferralSystem'
import LStatusChip from '@/components/common/LStatusChip.vue'

const { refreshRegistrationStatus } = useReferralSystem()

const loading = ref(true)
const initialLoadDone = ref(false)
const showSecret = ref(false)

// Section save states: 'idle' | 'saving' | 'saved' | 'error'
const sectionStates = reactive({
  crawler: 'idle',
  crawlerDefaults: 'idle',
  rag: 'idle',
  llmLogging: 'idle',
  referral: 'idle',
  aiAssistant: 'idle',
  zotero: 'idle'
})

// Debounce timers
const saveTimers = {}

const snackbar = reactive({
  show: false,
  text: '',
  color: 'error'
})

const settings = reactive({
  crawl_timeout_seconds: 3600,
  embedding_timeout_seconds: 7200,
  crawler_default_max_pages: 500,
  crawler_default_max_depth: 3,
  rag_default_chunk_size: 1000,
  rag_default_chunk_overlap: 200,
  llm_ai_log_responses: true,
  llm_ai_log_tasks: 'authenticity',
  llm_ai_log_response_max: 800,
  llm_ai_log_prompts: false,
  llm_ai_log_prompt_max: 800,
  referral_system_enabled: false,
  self_registration_enabled: false,
  default_referral_role: 'evaluator',
  ai_assistant_enabled: true,
  ai_assistant_color: '#9B59B6',
  ai_assistant_username: 'LLARS KI',
  updated_at: null
})

const availableRoles = [
  { value: 'evaluator', label: 'Evaluator' },
  { value: 'researcher', label: 'Researcher' },
  { value: 'chatbot_manager', label: 'Chatbot Manager' }
]

// AI Assistant color swatches (distinct colors for the AI)
const aiColorSwatches = [
  ['#9B59B6', '#8E44AD', '#6C3483'], // Purple variants (default)
  ['#3498DB', '#2980B9', '#1F618D'], // Blue variants
  ['#1ABC9C', '#16A085', '#117A65'], // Teal variants
  ['#E74C3C', '#C0392B', '#922B21']  // Red variants
]

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

const zoteroStatusLabel = computed(() => {
  if (zoteroStatus.active_source === 'env') return 'Aktiv (.env)'
  if (zoteroStatus.active_source === 'database') return 'Aktiv (DB)'
  return 'Nicht konfiguriert'
})

// Generic auto-save function for settings
async function saveSettingsSection(sectionKey, fields) {
  sectionStates[sectionKey] = 'saving'

  try {
    const payload = {}
    fields.forEach(field => {
      payload[field] = settings[field]
    })

    const response = await axios.patch('/api/admin/system/settings', payload)

    if (response.data.success) {
      // Update original settings
      fields.forEach(field => {
        originalSettings.value[field] = settings[field]
      })

      sectionStates[sectionKey] = 'saved'

      // If referral settings changed, refresh registration status
      if (sectionKey === 'referral') {
        await refreshRegistrationStatus()
      }

      // Clear "saved" state after 3 seconds
      setTimeout(() => {
        if (sectionStates[sectionKey] === 'saved') {
          sectionStates[sectionKey] = 'idle'
        }
      }, 3000)
    }
  } catch (error) {
    logI18nParams('error', 'logs.admin.systemSettings.saveSectionFailed', { section: sectionKey }, error)
    sectionStates[sectionKey] = 'error'
    snackbar.text = `Fehler beim Speichern: ${error.response?.data?.error || error.message}`
    snackbar.show = true

    // Clear error state after 5 seconds
    setTimeout(() => {
      if (sectionStates[sectionKey] === 'error') {
        sectionStates[sectionKey] = 'idle'
      }
    }, 5000)
  }
}

// Debounced save for each section
function debouncedSave(sectionKey, fields, delay = 500) {
  if (saveTimers[sectionKey]) {
    clearTimeout(saveTimers[sectionKey])
  }
  saveTimers[sectionKey] = setTimeout(() => {
    saveSettingsSection(sectionKey, fields)
  }, delay)
}

// Watch Crawler Timeouts
watch(
  () => [settings.crawl_timeout_seconds, settings.embedding_timeout_seconds],
  () => {
    if (!initialLoadDone.value) return
    debouncedSave('crawler', ['crawl_timeout_seconds', 'embedding_timeout_seconds'])
  }
)

// Watch Crawler Defaults
watch(
  () => [settings.crawler_default_max_pages, settings.crawler_default_max_depth],
  () => {
    if (!initialLoadDone.value) return
    debouncedSave('crawlerDefaults', ['crawler_default_max_pages', 'crawler_default_max_depth'])
  }
)

// Watch RAG Settings
watch(
  () => [settings.rag_default_chunk_size, settings.rag_default_chunk_overlap],
  () => {
    if (!initialLoadDone.value) return
    debouncedSave('rag', ['rag_default_chunk_size', 'rag_default_chunk_overlap'])
  }
)

// Watch LLM Logging Settings
watch(
  () => [
    settings.llm_ai_log_responses,
    settings.llm_ai_log_prompts,
    settings.llm_ai_log_tasks,
    settings.llm_ai_log_response_max,
    settings.llm_ai_log_prompt_max
  ],
  () => {
    if (!initialLoadDone.value) return
    debouncedSave('llmLogging', [
      'llm_ai_log_responses',
      'llm_ai_log_prompts',
      'llm_ai_log_tasks',
      'llm_ai_log_response_max',
      'llm_ai_log_prompt_max'
    ])
  }
)

// Watch Referral Settings
watch(
  () => [
    settings.referral_system_enabled,
    settings.self_registration_enabled,
    settings.default_referral_role
  ],
  () => {
    if (!initialLoadDone.value) return

    // If referral system is disabled, also disable self-registration
    if (!settings.referral_system_enabled && settings.self_registration_enabled) {
      settings.self_registration_enabled = false
    }

    debouncedSave('referral', [
      'referral_system_enabled',
      'self_registration_enabled',
      'default_referral_role'
    ], 300) // Faster for switches
  }
)

// Watch AI Assistant Settings
watch(
  () => [
    settings.ai_assistant_enabled,
    settings.ai_assistant_color,
    settings.ai_assistant_username
  ],
  () => {
    if (!initialLoadDone.value) return
    debouncedSave('aiAssistant', [
      'ai_assistant_enabled',
      'ai_assistant_color',
      'ai_assistant_username'
    ], 300)
  }
)

// Watch Zotero settings
watch(
  () => [zoteroDb.enabled, zoteroDb.client_key, zoteroDb.client_secret],
  () => {
    if (!initialLoadDone.value) return
    debouncedSaveZotero()
  }
)

let zoteroSaveTimer = null
function debouncedSaveZotero() {
  if (zoteroSaveTimer) clearTimeout(zoteroSaveTimer)
  zoteroSaveTimer = setTimeout(saveZoteroSettings, 500)
}

async function saveZoteroSettings() {
  sectionStates.zotero = 'saving'

  try {
    const payload = {
      enabled: zoteroDb.enabled,
      client_key: zoteroDb.client_key
    }
    if (zoteroDb.client_secret) {
      payload.client_secret = zoteroDb.client_secret
    }

    const response = await axios.patch('/api/admin/system/zotero-oauth', payload)

    if (response.data.success) {
      const z = response.data.zotero_oauth
      Object.assign(zoteroStatus, z)

      zoteroDb.client_secret = ''
      originalZoteroDb.value = {
        enabled: z.database?.enabled || false,
        client_key: z.database?.client_key || ''
      }

      sectionStates.zotero = 'saved'

      setTimeout(() => {
        if (sectionStates.zotero === 'saved') {
          sectionStates.zotero = 'idle'
        }
      }, 3000)
    }
  } catch (error) {
    logI18n('error', 'logs.admin.systemSettings.saveZoteroOauthFailed', error)
    sectionStates.zotero = 'error'
    snackbar.text = 'Fehler beim Speichern der Zotero-Einstellungen'
    snackbar.show = true

    setTimeout(() => {
      if (sectionStates.zotero === 'error') {
        sectionStates.zotero = 'idle'
      }
    }, 5000)
  }
}

async function loadSettings() {
  loading.value = true
  try {
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

      zoteroDb.enabled = z.database?.enabled || false
      zoteroDb.client_key = z.database?.client_key || ''
      zoteroDb.client_secret = ''
      originalZoteroDb.value = {
        enabled: z.database?.enabled || false,
        client_key: z.database?.client_key || ''
      }
    }

    // Enable watches after initial load
    initialLoadDone.value = true
  } catch (error) {
    logI18n('error', 'logs.admin.systemSettings.loadSettingsFailed', error)
    snackbar.text = 'Fehler beim Laden der Einstellungen'
    snackbar.show = true
  } finally {
    loading.value = false
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

.color-preview {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.12);
  transition: transform 0.15s, box-shadow 0.15s;
}

.color-preview:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.ai-preview-card {
  background: rgba(var(--v-theme-on-surface), 0.04);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.ai-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
