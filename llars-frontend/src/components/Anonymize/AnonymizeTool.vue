<template>
  <v-container fluid class="anonymize-page" :class="{ 'is-mobile': isMobile }">
    <v-row class="mb-4 align-center">
      <v-col cols="12" md="6">
        <div class="d-flex align-center flex-wrap gap-2">
          <h1 class="page-title">{{ $t('anonymization.title') }}</h1>
          <LInfoTooltip :title="$t('anonymization.tooltip.title')" :max-width="420">
            <div class="anonymize-info">
              <div>{{ $t('anonymization.tooltip.line1') }}</div>
              <div>{{ $t('anonymization.tooltip.line2') }}</div>
              <div>{{ $t('anonymization.tooltip.line3') }}</div>
            </div>
          </LInfoTooltip>
          <v-chip
            size="small"
            variant="tonal"
            :color="healthChip.color"
            :title="healthChip.title"
          >
            {{ healthChip.text }}
          </v-chip>
        </div>
        <p class="page-subtitle">{{ $t('anonymization.subtitle') }}</p>
      </v-col>
      <v-col cols="12" md="6" class="d-flex flex-wrap justify-end gap-2">
        <LBtn
          variant="secondary"
          prepend-icon="mdi-content-paste"
          :disabled="!hasPermission('feature:anonymize:view') || isLoading('process')"
          @click="pasteFromClipboard"
        >
          {{ $t('anonymization.actions.paste') }}
        </LBtn>
        <LBtn
          variant="secondary"
          prepend-icon="mdi-lightbulb-on-outline"
          :disabled="!hasPermission('feature:anonymize:view') || isLoading('process')"
          @click="loadExample"
        >
          {{ $t('anonymization.actions.loadExample') }}
        </LBtn>
        <LBtn
          variant="secondary"
          prepend-icon="mdi-content-copy"
          :disabled="!outputText || !hasPermission('feature:anonymize:view') || isLoading('process')"
          @click="copyToClipboard"
        >
          {{ $t('anonymization.actions.copyOutput') }}
        </LBtn>
        <LBtn
          variant="primary"
          prepend-icon="mdi-shield-lock-outline"
          :disabled="!inputText || !engineReady || !hasPermission('feature:anonymize:view') || isLoading('process')"
          @click="runPseudonymize"
        >
          {{ $t('anonymization.actions.pseudonymize') }}
        </LBtn>
        <LBtn
          variant="secondary"
          prepend-icon="mdi-refresh"
          :disabled="!inputText || !engineReady || !hasPermission('feature:anonymize:view') || isLoading('process')"
          @click="resetAndRun"
        >
          {{ $t('anonymization.actions.recalculate') }}
        </LBtn>

        <v-file-input
          v-model="selectedFile"
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          :label="$t('anonymization.fileInput.label')"
          density="compact"
          variant="outlined"
          hide-details
          class="file-input"
          :disabled="!engineReady || !hasPermission('feature:anonymize:view') || isLoading('process')"
          @update:model-value="handleFileSelected"
        />

        <v-btn variant="tonal" color="primary" icon @click="settingsDialogOpen = true" :title="$t('anonymization.actions.settings')">
          <LIcon>mdi-tune</LIcon>
        </v-btn>
      </v-col>
    </v-row>

    <v-alert v-if="errorMessage" type="error" variant="tonal" class="mb-4" closable @click:close="errorMessage = ''">
      {{ errorMessage }}
    </v-alert>
    <v-alert v-if="infoMessage" type="info" variant="tonal" class="mb-4" closable @click:close="infoMessage = ''">
      {{ infoMessage }}
    </v-alert>

    <v-row dense>
      <v-col cols="12" lg="4">
        <v-card class="panel-card">
          <v-card-title class="panel-title">
            <LIcon class="mr-2">mdi-text</LIcon>
            {{ $t('anonymization.sections.input') }}
          </v-card-title>
          <v-divider />
          <v-card-text>
            <v-progress-linear v-if="isLoading('process')" indeterminate height="2" class="mb-3" />

            <v-textarea
              v-model="inputText"
              :label="$t('anonymization.input.label')"
              :placeholder="$t('anonymization.input.placeholder')"
              rows="10"
              auto-grow
              density="compact"
              variant="outlined"
              hide-details
              :disabled="!hasPermission('feature:anonymize:view')"
            />

            <div class="preview-title mt-4">{{ $t('anonymization.preview.title') }}</div>
            <div class="text-renderer mt-2">
              <template v-for="(seg, idx) in inputSegments" :key="'in-' + idx">
                <span v-if="!seg.label">{{ seg.text }}</span>
                <mark v-else :class="['ent', `ent-${seg.label}`]">
                  {{ seg.text }}
                  <span class="ent-label">{{ seg.label }}</span>
                </mark>
              </template>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" lg="4">
        <v-card class="panel-card">
          <v-card-title class="panel-title">
            <LIcon class="mr-2">mdi-text-box-check-outline</LIcon>
            {{ $t('anonymization.sections.output') }}
          </v-card-title>
          <v-divider />
          <v-card-text>
            <v-progress-linear v-if="isLoading('process')" indeterminate height="2" class="mb-3" />

            <v-textarea
              v-model="outputText"
              :label="$t('anonymization.output.label')"
              :placeholder="$t('anonymization.output.placeholder')"
              rows="10"
              auto-grow
              density="compact"
              variant="outlined"
              hide-details
              readonly
            />

            <div class="preview-title mt-4">{{ $t('anonymization.preview.title') }}</div>
            <div class="text-renderer mt-2">
              <template v-for="(seg, idx) in outputSegments" :key="'out-' + idx">
                <span v-if="!seg.label">{{ seg.text }}</span>
                <mark v-else :class="['ent', `ent-${seg.label}`]">
                  {{ seg.text }}
                  <span class="ent-label">{{ seg.label }}</span>
                </mark>
              </template>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" lg="4">
        <v-card class="panel-card">
          <v-card-title class="panel-title">
            <LIcon class="mr-2">mdi-format-list-bulleted</LIcon>
            {{ $t('anonymization.sections.entities') }}
            <v-spacer />
            <v-chip size="small" variant="tonal">{{ groups.length }}</v-chip>
          </v-card-title>
          <v-divider />
          <v-card-text>
            <v-skeleton-loader v-if="isLoading('process')" type="list-item-two-line@6" />

            <div v-else>
              <div v-if="groups.length === 0" class="empty-state">
                {{ $t('anonymization.entities.empty') }}
              </div>

              <v-expansion-panels v-else variant="accordion" multiple>
                <v-expansion-panel v-for="g in groups" :key="g.group_id">
                  <v-expansion-panel-title>
                    <v-chip size="small" class="mr-2" variant="flat" :color="labelColor(g.label)">
                      {{ g.label }}
                    </v-chip>
                    <span class="entity-original">{{ g.original }}</span>
                    <v-spacer />
                    <v-chip size="x-small" variant="tonal">x{{ g.count }}</v-chip>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-row dense>
                      <v-col cols="12">
                        <v-text-field
                          v-model="g.replacement"
                          :label="$t('anonymization.entities.replacementLabel')"
                          density="compact"
                          variant="outlined"
                          hide-details
                          @blur="applyManual(g)"
                          @keyup.enter="applyManual(g)"
                        />
                      </v-col>
                      <v-col cols="12" class="d-flex align-center justify-space-between">
                        <div class="d-flex flex-wrap gap-2">
                          <v-chip size="small" variant="tonal">{{ $t('anonymization.entities.modeLabel', { mode: g.mode }) }}</v-chip>
                          <v-chip
                            v-if="g.db_hit !== null && g.db_hit !== undefined"
                            size="small"
                            variant="tonal"
                            :color="g.db_hit ? 'success' : 'warning'"
                          >
                            {{ $t('anonymization.entities.dbLabel', { status: g.db_hit ? $t('common.yes') : $t('common.no') }) }}
                          </v-chip>
                        </div>

                        <v-btn
                          v-if="g.can_randomize"
                          size="small"
                          variant="tonal"
                          color="primary"
                          :disabled="isLoading('process')"
                          @click="randomizeGroup(g)"
                        >
                          <LIcon start size="small">mdi-shuffle</LIcon>
                          {{ $t('anonymization.actions.randomize') }}
                        </v-btn>
                      </v-col>
                    </v-row>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="settingsDialogOpen" max-width="520">
      <v-card>
        <v-card-title>{{ $t('anonymization.settings.title') }}</v-card-title>
        <v-divider />
        <v-card-text>
          <v-row dense>
            <v-col cols="12">
              <v-select
                v-model="engine"
                :items="engineOptions"
                :label="$t('anonymization.settings.engine.label')"
                density="compact"
                variant="outlined"
                hide-details
              />
              <v-alert
                v-if="engine !== 'offline'"
                type="warning"
                variant="tonal"
                class="mt-3"
                density="compact"
              >
                {{ $t('anonymization.settings.engine.warning') }}
              </v-alert>
            </v-col>
            <v-col cols="12" v-if="engine !== 'offline'">
              <LlmModelSelect
                v-model="llmModel"
                :label="$t('anonymization.settings.llmModelLabel')"
                density="compact"
                :clearable="true"
                :auto-select-default="false"
                :hide-details="true"
              />
              <div class="settings-hint mt-2">
                {{ $t('anonymization.settings.llmStatus', { status: llmReady ? $t('anonymization.settings.llmReady') : $t('anonymization.settings.llmNotReady') }) }}
              </div>
            </v-col>
            <v-col cols="12">
              <v-select
                v-model="nameOrigin"
                :items="nameOriginOptions"
                :label="$t('anonymization.settings.nameOriginLabel')"
                density="compact"
                variant="outlined"
                hide-details
              />
            </v-col>
            <v-col cols="12">
              <v-text-field
                v-model.number="nameCount"
                type="number"
                min="0"
                step="1"
                :label="$t('anonymization.settings.nameCountLabel')"
                density="compact"
                variant="outlined"
                hide-details
              />
              <div class="settings-hint mt-2">
                {{ $t('anonymization.settings.nameCountHint') }}
              </div>
            </v-col>
          </v-row>
        </v-card-text>
        <v-divider />
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="settingsDialogOpen = false">{{ $t('common.close') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { BASE_URL } from '@/config.js'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { usePermissions } from '@/composables/usePermissions'
import { useMobile } from '@/composables/useMobile'
import LlmModelSelect from '@/components/common/LlmModelSelect.vue'

const { isMobile } = useMobile()
const { t } = useI18n()

const { isLoading, withLoading } = useSkeletonLoading([])
const { hasPermission, fetchPermissions, isLoading: permissionsLoading } = usePermissions()

const inputText = ref('')
const outputText = ref('')
const entities = ref([])
const groups = ref([])
const dateShiftDays = ref(null)
const anonymizeStatus = ref(null)

const liveMode = ref(true)
const ignoreNextInputWatch = ref(0)
const liveQueued = ref(false)
let liveTimer = null
const LIVE_DEBOUNCE_MS = 450

const selectedFile = ref(null)
const errorMessage = ref('')
const infoMessage = ref('')

const settingsDialogOpen = ref(false)

const engine = ref('offline')
const llmModel = ref('')
const engineOptions = computed(() => ([
  { title: t('anonymization.engineOptions.offline'), value: 'offline' },
  { title: t('anonymization.engineOptions.llm'), value: 'llm' },
  { title: t('anonymization.engineOptions.hybrid'), value: 'hybrid' }
]))

const nameOrigin = ref('Swiss_DE')
const nameCount = ref(1000)
const nameOriginOptions = computed(() => ([
  { title: t('anonymization.nameOrigins.swissDe'), value: 'Swiss_DE' },
  { title: t('anonymization.nameOrigins.swissFr'), value: 'Swiss_FR' },
  { title: t('anonymization.nameOrigins.swissIt'), value: 'Swiss_IT' },
  { title: t('anonymization.nameOrigins.swissRm'), value: 'Swiss_RM' },
  { title: t('anonymization.nameOrigins.germany'), value: 'German' }
]))

function clearLiveTimer() {
  if (liveTimer) {
    clearTimeout(liveTimer)
    liveTimer = null
  }
}

function scheduleLivePseudonymize({ immediate = false } = {}) {
  if (!liveMode.value) return
  if (!hasPermission('feature:anonymize:view')) return
  if (!anonymizeStatus.value) {
    liveQueued.value = true
    return
  }

  const text = inputText.value || ''
  if (text.trim() === '') {
    outputText.value = ''
    entities.value = []
    groups.value = []
    dateShiftDays.value = null
    return
  }

  if (isLoading('process')) {
    liveQueued.value = true
    return
  }

  // Don't attempt auto-run while engine isn't ready (would just produce an error toast loop).
  if (!engineReady.value) return

  clearLiveTimer()
  const delay = immediate ? 0 : LIVE_DEBOUNCE_MS
  liveTimer = setTimeout(() => {
    liveTimer = null
    runPseudonymize()
  }, delay)
}

function triggerLivePseudonymizeNow() {
  scheduleLivePseudonymize({ immediate: true })
}

const offlineReady = computed(() => anonymizeStatus.value?.ready === true)
const llmReady = computed(() => anonymizeStatus.value?.llm?.ready === true)
const engineReady = computed(() => {
  if (!anonymizeStatus.value) return true
  if (engine.value === 'llm') return llmReady.value
  if (engine.value === 'hybrid') return offlineReady.value && llmReady.value
  return offlineReady.value
})

function buildNotReadyMessage(status) {
  const files = status?.files || {}
  const missing = Object.entries(files)
    .filter(([, ok]) => ok === false)
    .map(([k]) => k)

  if (missing.length === 0) return t('anonymization.messages.resourcesNotReady')
  return t('anonymization.messages.resourcesMissing', { resources: missing.join(', ') })
}

function buildLlmNotReadyMessage(llmStatus) {
  if (!llmStatus) return t('anonymization.messages.llmNotConfigured')
  if (llmStatus.provider === 'litellm' && !llmStatus.base_url) {
    return t('anonymization.messages.llmMissingBaseUrl')
  }
  return t('anonymization.messages.llmMissingApiKey')
}

function extractApiError(e, fallback) {
  const data = e?.response?.data
  if (typeof data?.error === 'string' && data.error.trim()) return data.error
  if (typeof data?.message === 'string' && data.message.trim()) return data.message
  if (typeof e?.message === 'string' && e.message.trim()) return e.message
  return fallback
}

const healthChip = computed(() => {
  if (isLoading('health')) {
    return { text: t('anonymization.health.checking.text'), color: 'info', title: t('anonymization.health.checking.title') }
  }
  if (permissionsLoading.value) {
    return { text: t('anonymization.health.permissions.text'), color: 'info', title: t('anonymization.health.permissions.title') }
  }
  if (!hasPermission('feature:anonymize:view')) {
    return {
      text: t('anonymization.health.noAccess.text'),
      color: 'warning',
      title: t('anonymization.health.noAccess.title', { permission: 'feature:anonymize:view' })
    }
  }
  if (!anonymizeStatus.value) {
    return { text: t('anonymization.health.unknown.text'), color: 'grey', title: t('anonymization.health.unknown.title') }
  }

  if (engine.value === 'llm') {
    if (llmReady.value) {
      const provider = anonymizeStatus.value?.llm?.provider ? ` (${anonymizeStatus.value.llm.provider})` : ''
      return {
        text: t('anonymization.health.llmReady.text', { provider }),
        color: 'success',
        title: t('anonymization.health.llmReady.title')
      }
    }
    return {
      text: t('anonymization.health.llmMissing.text'),
      color: 'warning',
      title: buildLlmNotReadyMessage(anonymizeStatus.value?.llm)
    }
  }

  if (engine.value === 'hybrid') {
    if (engineReady.value) {
      return {
        text: t('anonymization.health.hybridReady.text'),
        color: 'success',
        title: t('anonymization.health.hybridReady.title')
      }
    }
    const missing = [
      offlineReady.value ? null : t('anonymization.health.missing.offline'),
      llmReady.value ? null : t('anonymization.health.missing.llm'),
    ].filter(Boolean)
    return {
      text: t('anonymization.health.hybridMissing.text'),
      color: 'warning',
      title: t('anonymization.health.hybridMissing.title', { missing: missing.join(' + ') })
    }
  }

  if (offlineReady.value) {
    return {
      text: t('anonymization.health.offlineReady.text'),
      color: 'success',
      title: t('anonymization.health.offlineReady.title')
    }
  }
  return {
    text: t('anonymization.health.offlineMissing.text'),
    color: 'warning',
    title: buildNotReadyMessage(anonymizeStatus.value)
  }
})

function labelColor(label) {
  switch (label) {
    case 'PER':
      return 'primary'
    case 'LOC':
      return 'success'
    case 'ORG':
      return 'teal'
    case 'DATE':
      return 'info'
    case 'AGE':
      return 'deep-purple'
    case 'PHONE':
      return 'warning'
    case 'MAIL':
      return 'secondary'
    case 'AHV':
      return 'error'
    case 'PLZ':
      return 'secondary'
    default:
      return 'grey'
  }
}

function buildSegments(text, spans, startKey, endKey) {
  const safeText = String(text || '')
  const sorted = [...(spans || [])].sort((a, b) => (a[startKey] - b[startKey]) || (a[endKey] - b[endKey]))
  const segments = []
  let cursor = 0

  for (const sp of sorted) {
    const s = Number(sp[startKey])
    const e = Number(sp[endKey])
    if (!Number.isFinite(s) || !Number.isFinite(e) || e <= s) continue
    if (s < cursor) continue
    segments.push({ text: safeText.slice(cursor, s), label: null })
    segments.push({ text: safeText.slice(s, e), label: sp.label })
    cursor = e
  }
  segments.push({ text: safeText.slice(cursor), label: null })
  return segments
}

const inputSegments = computed(() => buildSegments(inputText.value, entities.value, 'start', 'end'))
const outputSegments = computed(() => buildSegments(outputText.value, entities.value, 'output_start', 'output_end'))

function buildGroupOverrides() {
  const overrides = {}
  for (const g of groups.value || []) {
    overrides[g.group_id] = { replacement: g.replacement, mode: g.mode }
  }
  return overrides
}

async function loadHealth() {
  if (!hasPermission('feature:anonymize:view')) {
    infoMessage.value = t('anonymization.messages.noPermission')
    return
  }

  errorMessage.value = ''
  infoMessage.value = ''

  try {
    await withLoading('health', async () => {
      const url = `${BASE_URL}/api/anonymize/health?mode=quick`
      const maxAttempts = 2
      const timeoutMs = 4000

      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
          const res = await axios.get(url, { timeout: timeoutMs })
          if (!res.data?.success) {
            throw new Error(t('anonymization.messages.healthCheckFailed'))
          }
          anonymizeStatus.value = res.data?.status || null
          if (!anonymizeStatus.value?.ready) {
            errorMessage.value = buildNotReadyMessage(anonymizeStatus.value)
          }
          return
        } catch (e) {
          const status = e?.response?.status
          const retryable = !status || status === 502 || status === 503 || status === 504
          if (!retryable || attempt >= maxAttempts) throw e
          await new Promise(resolve => setTimeout(resolve, 400 * attempt))
        }
      }
    })
  } catch (e) {
    errorMessage.value = extractApiError(e, t('anonymization.messages.healthCheckFailed'))
  } finally {
    if (liveQueued.value && anonymizeStatus.value) {
      liveQueued.value = false
      triggerLivePseudonymizeNow()
    }
  }
}

async function runPseudonymize(action = null) {
  clearLiveTimer()
  errorMessage.value = ''
  infoMessage.value = ''

  if (!hasPermission('feature:anonymize:view')) {
    infoMessage.value = t('anonymization.messages.noPermission')
    return
  }

  try {
    await withLoading('process', async () => {
      const payload = {
        text: inputText.value,
        group_overrides: buildGroupOverrides(),
        date_shift_days: dateShiftDays.value,
        action,
        name_origin: nameOrigin.value,
        name_count: nameCount.value,
        engine: engine.value,
        llm_model: llmModel.value || null
      }

      const res = await axios.post(`${BASE_URL}/api/anonymize/pseudonymize`, payload)
      if (!res.data?.success) {
        throw new Error(res.data?.error || t('anonymization.messages.pseudonymizeFailed'))
      }

      ignoreNextInputWatch.value += 1
      inputText.value = res.data.input_text || ''
      outputText.value = res.data.output_text || ''
      entities.value = res.data.entities || []
      groups.value = res.data.groups || []
      dateShiftDays.value = Number.isFinite(res.data.date_shift_days) ? res.data.date_shift_days : dateShiftDays.value
      anonymizeStatus.value = { ...(anonymizeStatus.value || {}), ready: true }
    })
  } catch (e) {
    const data = e?.response?.data
    if (data?.code === 'ANONYMIZE_NOT_READY' && data?.status) {
      anonymizeStatus.value = data.status
      errorMessage.value = buildNotReadyMessage(data.status)
      return
    }
    if (data?.code === 'ANONYMIZE_LLM_NOT_READY' && data?.status) {
      anonymizeStatus.value = { ...(anonymizeStatus.value || {}), llm: data.status, ready: anonymizeStatus.value?.ready }
      errorMessage.value = buildLlmNotReadyMessage(data.status)
      return
    }
    errorMessage.value = extractApiError(e, t('anonymization.messages.pseudonymizeFailed'))
  } finally {
    if (liveQueued.value) {
      liveQueued.value = false
      triggerLivePseudonymizeNow()
    }
  }
}

async function randomizeGroup(group) {
  await runPseudonymize({ type: 'randomize', group_id: group.group_id })
}

/**
 * Apply replacements locally without calling the backend.
 * This is much faster when only aliases change (no NER re-detection needed).
 */
function applyReplacementsLocally() {
  const text = inputText.value || ''
  if (!text || entities.value.length === 0) return

  // Build group_id → replacement map
  const replacementMap = {}
  for (const g of groups.value) {
    replacementMap[g.group_id] = g.replacement || g.original
  }

  // Sort entities by start position (ascending)
  const sortedEntities = [...entities.value].sort((a, b) => a.start - b.start)

  // Build output text by replacing entity spans
  let output = ''
  let cursor = 0
  let offset = 0 // Track position difference between input and output

  for (const ent of sortedEntities) {
    const start = ent.start
    const end = ent.end
    const replacement = replacementMap[ent.group_id] || text.slice(start, end)

    // Add text before this entity
    output += text.slice(cursor, start)

    // Calculate new output positions
    const outputStart = start + offset
    ent.output_start = outputStart
    ent.output_end = outputStart + replacement.length

    // Add replacement
    output += replacement

    // Update offset (difference between original length and replacement length)
    offset += replacement.length - (end - start)
    cursor = end
  }

  // Add remaining text after last entity
  output += text.slice(cursor)

  outputText.value = output
}

function applyManual(group) {
  if (!group) return
  group.mode = 'manual'
  // Use local replacement - no backend call needed!
  applyReplacementsLocally()
}

async function resetAndRun() {
  errorMessage.value = ''
  infoMessage.value = ''
  outputText.value = ''
  entities.value = []
  groups.value = []
  dateShiftDays.value = null
  await runPseudonymize()
}

async function pasteFromClipboard() {
  errorMessage.value = ''
  infoMessage.value = ''

  try {
    const text = await navigator.clipboard.readText()
    ignoreNextInputWatch.value += 1
    inputText.value = text || ''
    outputText.value = ''
    entities.value = []
    groups.value = []
    dateShiftDays.value = null
    await runPseudonymize()
  } catch (e) {
    errorMessage.value = t('anonymization.messages.clipboardReadFailed')
  }
}

async function copyToClipboard() {
  errorMessage.value = ''
  infoMessage.value = ''

  try {
    await navigator.clipboard.writeText(outputText.value || '')
    infoMessage.value = t('anonymization.messages.clipboardCopySuccess')
  } catch (e) {
    errorMessage.value = t('anonymization.messages.clipboardCopyFailed')
  }
}

async function handleFileSelected(fileOrFiles) {
  const file = Array.isArray(fileOrFiles) ? fileOrFiles[0] : fileOrFiles
  if (!file) return

  errorMessage.value = ''
  infoMessage.value = ''
  outputText.value = ''
  entities.value = []
  groups.value = []
  dateShiftDays.value = null

  try {
    await withLoading('process', async () => {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('name_origin', nameOrigin.value)
      fd.append('name_count', String(nameCount.value))
      fd.append('engine', engine.value)
      if (llmModel.value) fd.append('llm_model', llmModel.value)
      const res = await axios.post(`${BASE_URL}/api/anonymize/pseudonymize-file`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      if (!res.data?.success) {
        throw new Error(res.data?.error || t('anonymization.messages.uploadFailed'))
      }

      ignoreNextInputWatch.value += 1
      inputText.value = res.data.input_text || ''
      outputText.value = res.data.output_text || ''
      entities.value = res.data.entities || []
      groups.value = res.data.groups || []
      dateShiftDays.value = Number.isFinite(res.data.date_shift_days) ? res.data.date_shift_days : dateShiftDays.value
      anonymizeStatus.value = { ...(anonymizeStatus.value || {}), ready: true }
    })
  } catch (e) {
    const data = e?.response?.data
    if (data?.code === 'ANONYMIZE_NOT_READY' && data?.status) {
      anonymizeStatus.value = data.status
      errorMessage.value = buildNotReadyMessage(data.status)
    } else if (data?.code === 'ANONYMIZE_LLM_NOT_READY' && data?.status) {
      anonymizeStatus.value = { ...(anonymizeStatus.value || {}), llm: data.status, ready: anonymizeStatus.value?.ready }
      errorMessage.value = buildLlmNotReadyMessage(data.status)
    } else {
      errorMessage.value = extractApiError(e, t('anonymization.messages.uploadFailed'))
    }
  }

  selectedFile.value = null
}

async function loadExample() {
  // Replace literal \n with actual newlines (JSON escaping produces literal \n)
  const example = t('anonymization.exampleText').replace(/\\n/g, '\n')

  errorMessage.value = ''
  infoMessage.value = ''
  outputText.value = ''
  entities.value = []
  groups.value = []
  dateShiftDays.value = null

  ignoreNextInputWatch.value += 1
  inputText.value = example
  await runPseudonymize()
}

watch(inputText, () => {
  if (ignoreNextInputWatch.value > 0) {
    ignoreNextInputWatch.value -= 1
    return
  }
  scheduleLivePseudonymize()
})

watch([engine, llmModel, nameOrigin, nameCount], () => {
  scheduleLivePseudonymize()
})

onBeforeUnmount(() => {
  clearLiveTimer()
})

onMounted(async () => {
  await fetchPermissions()
  loadHealth()
})
</script>

<style scoped>
.anonymize-page {
  background-color: rgb(var(--v-theme-background));
  min-height: calc(100vh - 94px);
  color: rgb(var(--v-theme-on-surface));
}

.page-title {
  margin: 0;
  color: rgb(var(--v-theme-on-surface));
}

.page-subtitle {
  margin: 4px 0 0;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.gap-2 {
  gap: 8px;
}

.file-input {
  max-width: 220px;
}

.panel-card {
  height: 100%;
}

.panel-title {
  color: rgb(var(--v-theme-on-surface));
}

.text-renderer {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: clamp(0.85rem, 0.8rem + 0.35vw, 1.05rem);
  line-height: 1.5;
  color: rgb(var(--v-theme-on-surface));
}

.ent {
  display: inline-block;
  padding: 0.2em 0.35em;
  margin: 0 0.08em;
  border-radius: 0.35em;
  line-height: 1.2;
  color: rgb(var(--v-theme-on-surface));
  background: rgba(var(--v-theme-surface-variant), 0.35);
}

.ent-label {
  display: inline-block;
  margin-left: 0.45em;
  padding: 0.15em 0.4em;
  border-radius: 0.35em;
  font-size: 0.72em;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: rgba(var(--v-theme-on-surface), 0.9);
  background: rgba(var(--v-theme-on-surface), 0.12);
}

.ent-PER {
  background: rgba(var(--v-theme-primary), 0.22);
}

.ent-LOC {
  background: rgba(var(--v-theme-success), 0.22);
}

.ent-ORG {
  background: rgba(var(--v-theme-success), 0.16);
}

.ent-DATE {
  background: rgba(var(--v-theme-info), 0.22);
}

.ent-AGE {
  background: rgba(var(--v-theme-primary), 0.14);
}

.ent-PHONE {
  background: rgba(var(--v-theme-warning), 0.22);
}

.ent-MAIL {
  background: rgba(var(--v-theme-secondary), 0.22);
}

.ent-AHV {
  background: rgba(var(--v-theme-error), 0.22);
}

.ent-PLZ {
  background: rgba(var(--v-theme-secondary), 0.18);
}

.entity-original {
  color: rgb(var(--v-theme-on-surface));
}

.empty-state {
  padding: 12px;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.init-overlay .overlay-text {
  color: rgb(var(--v-theme-on-surface));
}

.preview-title {
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: rgba(var(--v-theme-on-surface), 0.75);
  text-transform: uppercase;
}

.anonymize-info {
  display: grid;
  gap: 6px;
}

.settings-hint {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

/* Mobile Styles */
.anonymize-page.is-mobile {
  max-width: 100vw;
  overflow-x: hidden;
  padding: 12px !important;
}

.anonymize-page.is-mobile .page-title {
  font-size: 1.25rem;
}

.anonymize-page.is-mobile .page-subtitle {
  font-size: 0.8rem;
}

.anonymize-page.is-mobile .file-input {
  max-width: 100%;
  width: 100%;
}

.anonymize-page.is-mobile :deep(.v-row.mb-4) {
  margin-bottom: 8px !important;
}

.anonymize-page.is-mobile :deep(.v-col) {
  padding: 6px !important;
}

.anonymize-page.is-mobile .panel-card {
  margin-bottom: 12px;
}

.anonymize-page.is-mobile .text-renderer {
  font-size: 0.85rem;
}

/* Stack action buttons vertically on mobile */
.anonymize-page.is-mobile :deep(.v-row.mb-4 .v-col:last-child) {
  flex-direction: column;
}

.anonymize-page.is-mobile :deep(.v-row.mb-4 .v-col:last-child .v-btn),
.anonymize-page.is-mobile :deep(.v-row.mb-4 .v-col:last-child .l-btn) {
  width: 100%;
}
</style>
