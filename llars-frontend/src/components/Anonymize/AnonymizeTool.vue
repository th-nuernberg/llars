<template>
  <v-container fluid class="anonymize-page" :class="{ 'is-mobile': isMobile }">
    <v-row class="mb-4 align-center">
      <v-col cols="12" md="6">
        <div class="d-flex align-center flex-wrap gap-2">
          <h1 class="page-title">Anonymisierung</h1>
          <LInfoTooltip title="Anonymisierung" :max-width="420">
            <div class="anonymize-info">
              <div>Beim ersten Laden kann es etwas dauern, bis lokale Modelle und die Datenbank bereit sind.</div>
              <div>Offline: Regeln + NER erkennen personenbezogene Daten, danach werden Treffer konsistent pseudonymisiert.</div>
              <div>LLM/Hybrid: zusätzliche LLM-Extraktion, Ergebnisse werden anschließend ebenfalls pseudonymisiert.</div>
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
        <p class="page-subtitle">Offline-Pseudonymisierung für deutsche Texte (DOCX/PDF/Clipboard)</p>
      </v-col>
      <v-col cols="12" md="6" class="d-flex flex-wrap justify-end gap-2">
        <LBtn
          variant="secondary"
          prepend-icon="mdi-content-paste"
          :disabled="!hasPermission('feature:anonymize:view') || isLoading('process')"
          @click="pasteFromClipboard"
        >
          Zwischenablage einfügen
        </LBtn>
        <LBtn
          variant="secondary"
          prepend-icon="mdi-lightbulb-on-outline"
          :disabled="!hasPermission('feature:anonymize:view') || isLoading('process')"
          @click="loadExample"
        >
          Beispiel laden
        </LBtn>
        <LBtn
          variant="secondary"
          prepend-icon="mdi-content-copy"
          :disabled="!outputText || !hasPermission('feature:anonymize:view') || isLoading('process')"
          @click="copyToClipboard"
        >
          Output kopieren
        </LBtn>
        <LBtn
          variant="primary"
          prepend-icon="mdi-shield-lock-outline"
          :disabled="!inputText || !engineReady || !hasPermission('feature:anonymize:view') || isLoading('process')"
          @click="runPseudonymize"
        >
          Pseudonymisieren
        </LBtn>
        <LBtn
          variant="secondary"
          prepend-icon="mdi-refresh"
          :disabled="!inputText || !engineReady || !hasPermission('feature:anonymize:view') || isLoading('process')"
          @click="resetAndRun"
        >
          Neu berechnen
        </LBtn>

        <v-file-input
          v-model="selectedFile"
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          label="DOCX/PDF"
          density="compact"
          variant="outlined"
          hide-details
          class="file-input"
          :disabled="!engineReady || !hasPermission('feature:anonymize:view') || isLoading('process')"
          @update:model-value="handleFileSelected"
        />

        <v-btn variant="tonal" color="primary" icon @click="settingsDialogOpen = true" :title="'Einstellungen'">
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
            Input
          </v-card-title>
          <v-divider />
          <v-card-text>
            <v-progress-linear v-if="isLoading('process')" indeterminate height="2" class="mb-3" />

            <v-textarea
              v-model="inputText"
              label="Text eingeben"
              placeholder="Hier Text einfügen oder tippen…"
              rows="10"
              auto-grow
              density="compact"
              variant="outlined"
              hide-details
              :disabled="!hasPermission('feature:anonymize:view')"
            />

            <div class="preview-title mt-4">Highlight Preview</div>
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
            Output
          </v-card-title>
          <v-divider />
          <v-card-text>
            <v-progress-linear v-if="isLoading('process')" indeterminate height="2" class="mb-3" />

            <v-textarea
              v-model="outputText"
              label="Output"
              placeholder="Output erscheint hier…"
              rows="10"
              auto-grow
              density="compact"
              variant="outlined"
              hide-details
              readonly
            />

            <div class="preview-title mt-4">Highlight Preview</div>
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
            Entitäten
            <v-spacer />
            <v-chip size="small" variant="tonal">{{ groups.length }}</v-chip>
          </v-card-title>
          <v-divider />
          <v-card-text>
            <v-skeleton-loader v-if="isLoading('process')" type="list-item-two-line@6" />

            <div v-else>
              <div v-if="groups.length === 0" class="empty-state">
                Keine Entitäten erkannt.
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
                          label="Ersatz"
                          density="compact"
                          variant="outlined"
                          hide-details
                          @blur="applyManual(g)"
                          @keyup.enter="applyManual(g)"
                        />
                      </v-col>
                      <v-col cols="12" class="d-flex align-center justify-space-between">
                        <div class="d-flex flex-wrap gap-2">
                          <v-chip size="small" variant="tonal">Modus: {{ g.mode }}</v-chip>
                          <v-chip
                            v-if="g.db_hit !== null && g.db_hit !== undefined"
                            size="small"
                            variant="tonal"
                            :color="g.db_hit ? 'success' : 'warning'"
                          >
                            DB: {{ g.db_hit ? 'True' : 'False' }}
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
                          Randomize
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
        <v-card-title>Einstellungen</v-card-title>
        <v-divider />
        <v-card-text>
          <v-row dense>
            <v-col cols="12">
              <v-select
                v-model="engine"
                :items="engineOptions"
                label="Engine"
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
                Der Text wird an das konfigurierte LLM gesendet (LiteLLM/OpenAI). Keine Offline-Garantie.
              </v-alert>
            </v-col>
            <v-col cols="12" v-if="engine !== 'offline'">
              <LlmModelSelect
                v-model="llmModel"
                label="LLM Modell (optional)"
                density="compact"
                :clearable="true"
                :auto-select-default="false"
                :hide-details="true"
              />
              <div class="settings-hint mt-2">
                Leer lassen = Backend-Default. Status: {{ llmReady ? 'bereit' : 'nicht bereit' }}
              </div>
            </v-col>
            <v-col cols="12">
              <v-select
                v-model="nameOrigin"
                :items="nameOriginOptions"
                label="Namensregion"
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
                label="Name Count (Häufigkeitsschwelle)"
                density="compact"
                variant="outlined"
                hide-details
              />
              <div class="settings-hint mt-2">
                Wirkt auf Auto-Ersetzungen bei „Neu berechnen“ oder bei neuem Input.
              </div>
            </v-col>
          </v-row>
        </v-card-text>
        <v-divider />
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="settingsDialogOpen = false">Schließen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import axios from 'axios'
import { BASE_URL } from '@/config.js'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { usePermissions } from '@/composables/usePermissions'
import { useMobile } from '@/composables/useMobile'
import LlmModelSelect from '@/components/common/LlmModelSelect.vue'

const { isMobile } = useMobile()

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
const engineOptions = [
  { title: 'Offline (lokal, Regeln + NER)', value: 'offline' },
  { title: 'LLM (Regeln + LLM-Extraktion)', value: 'llm' },
  { title: 'Hybrid (Offline + LLM)', value: 'hybrid' }
]

const nameOrigin = ref('Swiss_DE')
const nameCount = ref(1000)
const nameOriginOptions = [
  { title: 'Schweiz (DE)', value: 'Swiss_DE' },
  { title: 'Schweiz (FR)', value: 'Swiss_FR' },
  { title: 'Schweiz (IT)', value: 'Swiss_IT' },
  { title: 'Schweiz (RM)', value: 'Swiss_RM' },
  { title: 'Deutschland', value: 'German' }
]

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

  if (missing.length === 0) return 'Anonymize Ressourcen/Modelle sind nicht bereit.'
  return `Anonymize Ressourcen fehlen: ${missing.join(', ')}`
}

function buildLlmNotReadyMessage(llmStatus) {
  if (!llmStatus) return 'LLM ist nicht konfiguriert.'
  if (llmStatus.provider === 'litellm' && !llmStatus.base_url) {
    return 'LiteLLM ist nicht konfiguriert (LITELLM_BASE_URL fehlt).'
  }
  return 'LLM ist nicht konfiguriert (OPENAI_API_KEY oder LITELLM_API_KEY fehlt).'
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
    return { text: 'Prüfe…', color: 'info', title: 'Prüft lokale Modelle/Datenbank…' }
  }
  if (permissionsLoading.value) {
    return { text: 'Prüfe…', color: 'info', title: 'Lade Berechtigungen…' }
  }
  if (!hasPermission('feature:anonymize:view')) {
    return { text: 'Kein Zugriff', color: 'warning', title: 'Keine Berechtigung: feature:anonymize:view' }
  }
  if (!anonymizeStatus.value) {
    return { text: 'Unbekannt', color: 'grey', title: 'Status noch nicht geprüft' }
  }

  if (engine.value === 'llm') {
    if (llmReady.value) {
      const provider = anonymizeStatus.value?.llm?.provider ? ` (${anonymizeStatus.value.llm.provider})` : ''
      return { text: `LLM bereit${provider}`, color: 'success', title: 'LLM ist verfügbar' }
    }
    return { text: 'LLM fehlt', color: 'warning', title: buildLlmNotReadyMessage(anonymizeStatus.value?.llm) }
  }

  if (engine.value === 'hybrid') {
    if (engineReady.value) {
      return { text: 'Hybrid bereit', color: 'success', title: 'Offline + LLM sind verfügbar' }
    }
    const missing = [
      offlineReady.value ? null : 'Offline Ressourcen',
      llmReady.value ? null : 'LLM',
    ].filter(Boolean)
    return { text: 'Hybrid fehlt', color: 'warning', title: `Nicht bereit: ${missing.join(' + ')}` }
  }

  if (offlineReady.value) {
    return { text: 'Bereit', color: 'success', title: 'Alle Anonymize Ressourcen sind verfügbar' }
  }
  return { text: 'Nicht bereit', color: 'warning', title: buildNotReadyMessage(anonymizeStatus.value) }
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
    infoMessage.value = 'Keine Berechtigung: feature:anonymize:view'
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
            throw new Error('Health-Check fehlgeschlagen')
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
    errorMessage.value = extractApiError(e, 'Health-Check fehlgeschlagen')
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
    infoMessage.value = 'Keine Berechtigung: feature:anonymize:view'
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
        throw new Error(res.data?.error || 'Pseudonymisierung fehlgeschlagen')
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
    errorMessage.value = extractApiError(e, 'Pseudonymisierung fehlgeschlagen')
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

async function applyManual(group) {
  if (!group) return
  group.mode = 'manual'
  await runPseudonymize()
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
    errorMessage.value = 'Zwischenablage konnte nicht gelesen werden.'
  }
}

async function copyToClipboard() {
  errorMessage.value = ''
  infoMessage.value = ''

  try {
    await navigator.clipboard.writeText(outputText.value || '')
    infoMessage.value = 'Output wurde in die Zwischenablage kopiert.'
  } catch (e) {
    errorMessage.value = 'Output konnte nicht in die Zwischenablage kopiert werden.'
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
        throw new Error(res.data?.error || 'Upload fehlgeschlagen')
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
      errorMessage.value = extractApiError(e, 'Upload fehlgeschlagen')
    }
  }

  selectedFile.value = null
}

async function loadExample() {
  const example = `Guten Tag Frau Müller,

mein Name ist Anna Müller (34) und ich wohne in 8001 Zürich.
Bitte kontaktieren Sie mich unter 079 123 45 67 oder via anna.mueller@example.ch.
Meine AHV-Nummer lautet 756.1234.5678.97.
Der Termin ist am 12.03.2024 um 14:30 Uhr bei der Universität Zürich.

Freundliche Grüsse
Anna Müller`

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
