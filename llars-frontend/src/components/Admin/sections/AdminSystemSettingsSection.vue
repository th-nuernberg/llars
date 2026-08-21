<template>
  <div class="system-settings-section">
    <v-card>
      <v-card-title class="d-flex align-center">
        <LIcon class="mr-2">mdi-cog</LIcon>
        {{ $t('admin.systemSettings.title') }}
      </v-card-title>
      <v-card-subtitle>
        {{ $t('admin.systemSettings.subtitle') }}
      </v-card-subtitle>

      <v-card-text>
        <v-skeleton-loader v-if="loading" type="article" />

        <template v-else>
          <!-- Crawler Timeouts -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-subtitle-1 d-flex align-center">
              <LIcon class="mr-2" size="small">mdi-timer-outline</LIcon>
              {{ $t('admin.systemSettings.crawlerTimeouts.title') }}
              <v-spacer />
              <LStatusChip :state="sectionStates.crawler" />
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.crawl_timeout_seconds"
                    :label="$t('admin.systemSettings.crawlerTimeouts.crawlTimeout')"
                    type="number"
                    :min="60"
                    :max="86400"
                    variant="outlined"
                    density="comfortable"
                    :hint="$t('admin.systemSettings.crawlerTimeouts.crawlTimeoutHint')"
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
                    :label="$t('admin.systemSettings.crawlerTimeouts.embeddingTimeout')"
                    type="number"
                    :min="60"
                    :max="86400"
                    variant="outlined"
                    density="comfortable"
                    :hint="$t('admin.systemSettings.crawlerTimeouts.embeddingTimeoutHint')"
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
              {{ $t('admin.systemSettings.crawlerDefaults.title') }}
              <v-spacer />
              <LStatusChip :state="sectionStates.crawlerDefaults" />
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.crawler_default_max_pages"
                    :label="$t('admin.systemSettings.crawlerDefaults.maxPages')"
                    type="number"
                    :min="1"
                    :max="10000"
                    variant="outlined"
                    density="comfortable"
                    :hint="$t('admin.systemSettings.crawlerDefaults.maxPagesHint')"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.crawler_default_max_depth"
                    :label="$t('admin.systemSettings.crawlerDefaults.maxDepth')"
                    type="number"
                    :min="1"
                    :max="10"
                    variant="outlined"
                    density="comfortable"
                    :hint="$t('admin.systemSettings.crawlerDefaults.maxDepthHint')"
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
              {{ $t('admin.systemSettings.ragChunking.title') }}
              <v-spacer />
              <LStatusChip :state="sectionStates.rag" />
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.rag_default_chunk_size"
                    :label="$t('admin.systemSettings.ragChunking.chunkSize')"
                    type="number"
                    :min="100"
                    :max="10000"
                    variant="outlined"
                    density="comfortable"
                    :hint="$t('admin.systemSettings.ragChunking.chunkSizeHint')"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.rag_default_chunk_overlap"
                    :label="$t('admin.systemSettings.ragChunking.chunkOverlap')"
                    type="number"
                    :min="0"
                    :max="5000"
                    variant="outlined"
                    density="comfortable"
                    :hint="$t('admin.systemSettings.ragChunking.chunkOverlapHint')"
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
              {{ $t('admin.systemSettings.llmLogging.title') }}
              <v-spacer />
              <LStatusChip :state="sectionStates.llmLogging" />
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" md="6">
                  <v-switch
                    v-model="settings.llm_ai_log_responses"
                    :label="$t('admin.systemSettings.llmLogging.logResponses')"
                    color="primary"
                    hide-details
                    density="compact"
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-switch
                    v-model="settings.llm_ai_log_prompts"
                    :label="$t('admin.systemSettings.llmLogging.logPrompts')"
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
                    :label="$t('admin.systemSettings.llmLogging.tasks')"
                    variant="outlined"
                    density="comfortable"
                    :hint="$t('admin.systemSettings.llmLogging.tasksHint')"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.llm_ai_log_response_max"
                    :label="$t('admin.systemSettings.llmLogging.maxResponseChars')"
                    type="number"
                    :min="0"
                    :max="10000"
                    variant="outlined"
                    density="comfortable"
                    :hint="$t('admin.systemSettings.llmLogging.defaultCharsHint')"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.llm_ai_log_prompt_max"
                    :label="$t('admin.systemSettings.llmLogging.maxPromptChars')"
                    type="number"
                    :min="0"
                    :max="10000"
                    variant="outlined"
                    density="comfortable"
                    :hint="$t('admin.systemSettings.llmLogging.defaultCharsHint')"
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
                {{ $t('admin.systemSettings.llmLogging.privacyWarning') }}
              </v-alert>
            </v-card-text>
          </v-card>

          <!-- Batch Generation Settings -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-subtitle-1 d-flex align-center">
              <LIcon class="mr-2" size="small">mdi-layers-triple-outline</LIcon>
              {{ $t('admin.systemSettings.batchGeneration.title') }}
              <v-spacer />
              <LStatusChip :state="sectionStates.batchGeneration" />
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="settings.batch_generation_max_parallel"
                    :label="$t('admin.systemSettings.batchGeneration.maxParallel')"
                    type="number"
                    :min="1"
                    :max="16"
                    variant="outlined"
                    density="comfortable"
                    :hint="$t('admin.systemSettings.batchGeneration.maxParallelHint')"
                    persistent-hint
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- Referral System Settings -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-subtitle-1 d-flex align-center">
              <LIcon class="mr-2" size="small">mdi-account-multiple-plus</LIcon>
              {{ $t('admin.systemSettings.referral.title') }}
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
                <span v-html="$t('admin.systemSettings.referral.info')"></span>
              </v-alert>

              <v-row>
                <v-col cols="12" md="6">
                  <v-switch
                    v-model="settings.referral_system_enabled"
                    :label="$t('admin.systemSettings.referral.enable')"
                    color="primary"
                    hide-details
                    density="compact"
                    class="mb-2"
                  />
                  <div class="text-caption text-medium-emphasis ml-10">
                    {{ $t('admin.systemSettings.referral.enableHint') }}
                  </div>
                </v-col>
                <v-col cols="12" md="6">
                  <v-switch
                    v-model="settings.self_registration_enabled"
                    :label="$t('admin.systemSettings.referral.selfRegistration')"
                    color="success"
                    hide-details
                    density="compact"
                    class="mb-2"
                    :disabled="!settings.referral_system_enabled"
                  />
                  <div class="text-caption text-medium-emphasis ml-10">
                    {{ $t('admin.systemSettings.referral.selfRegistrationHint') }}
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
                    :label="$t('admin.systemSettings.referral.defaultRole')"
                    variant="outlined"
                    density="comfortable"
                    :hint="$t('admin.systemSettings.referral.defaultRoleHint')"
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
                {{ $t('admin.systemSettings.referral.activeAlert') }}
              </v-alert>
            </v-card-text>
          </v-card>

          <!-- Self-Service Password Reset Settings -->
          <v-card variant="outlined" class="mb-4">
            <v-card-title class="text-subtitle-1 d-flex align-center">
              <LIcon class="mr-2" size="small">mdi-lock-reset</LIcon>
              {{ $t('admin.systemSettings.passwordReset.title') }}
              <v-spacer />
              <LStatusChip :state="sectionStates.passwordReset" />
            </v-card-title>
            <v-card-text>
              <v-alert
                type="info"
                variant="tonal"
                density="compact"
                class="mb-4"
              >
                {{ $t('admin.systemSettings.passwordReset.info') }}
              </v-alert>

              <v-row>
                <v-col cols="12" md="6">
                  <v-switch
                    v-model="settings.self_service_password_reset_enabled"
                    :label="$t('admin.systemSettings.passwordReset.enable')"
                    color="primary"
                    hide-details
                    density="compact"
                    class="mb-2"
                  />
                  <div class="text-caption text-medium-emphasis ml-10">
                    {{ $t('admin.systemSettings.passwordReset.enableHint') }}
                  </div>
                </v-col>
              </v-row>

              <v-alert
                v-if="settings.self_service_password_reset_enabled"
                type="success"
                variant="tonal"
                density="compact"
                class="mt-4"
              >
                <LIcon start size="small">mdi-check-circle</LIcon>
                {{ $t('admin.systemSettings.passwordReset.activeAlert') }}
              </v-alert>
            </v-card-text>
          </v-card>

          <!-- Last updated info -->
          <div v-if="settings.updated_at" class="text-caption text-medium-emphasis mt-4">
            {{ $t('admin.systemSettings.lastUpdated', { date: formatDate(settings.updated_at) }) }}
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
import { ref, reactive, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { logI18n, logI18nParams } from '@/utils/logI18n'
import { useReferralSystem } from '@/composables/useReferralSystem'
import LStatusChip from '@/components/common/LStatusChip.vue'

const { t } = useI18n()

const { refreshRegistrationStatus } = useReferralSystem()

const loading = ref(true)
const initialLoadDone = ref(false)

// Section save states: 'idle' | 'saving' | 'saved' | 'error'
const sectionStates = reactive({
  crawler: 'idle',
  crawlerDefaults: 'idle',
  rag: 'idle',
  llmLogging: 'idle',
  batchGeneration: 'idle',
  referral: 'idle',
  passwordReset: 'idle'
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
  batch_generation_max_parallel: 4,
  referral_system_enabled: false,
  self_registration_enabled: false,
  default_referral_role: 'evaluator',
  self_service_password_reset_enabled: false,
  updated_at: null
})

const availableRoles = [
  { value: 'evaluator', label: 'Evaluator' },
  { value: 'researcher', label: 'Researcher' },
  { value: 'chatbot_manager', label: 'Chatbot Manager' }
]

const originalSettings = ref({})

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
    snackbar.text = t('admin.systemSettings.errors.saveFailed', { error: error.response?.data?.error || error.message })
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

// Watch Batch Generation Settings
watch(
  () => [settings.batch_generation_max_parallel],
  () => {
    if (!initialLoadDone.value) return
    debouncedSave('batchGeneration', ['batch_generation_max_parallel'])
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

// Watch Self-Service Password Reset Settings
watch(
  () => [settings.self_service_password_reset_enabled],
  () => {
    if (!initialLoadDone.value) return
    debouncedSave('passwordReset', ['self_service_password_reset_enabled'], 300)
  }
)

async function loadSettings() {
  loading.value = true
  try {
    const settingsRes = await axios.get('/api/admin/system/settings')

    if (settingsRes.data.success) {
      Object.assign(settings, settingsRes.data.settings)
      originalSettings.value = { ...settingsRes.data.settings }
    }

    // Enable watches after initial load
    initialLoadDone.value = true
  } catch (error) {
    logI18n('error', 'logs.admin.systemSettings.loadSettingsFailed', error)
    snackbar.text = t('admin.systemSettings.errors.loadFailed')
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
