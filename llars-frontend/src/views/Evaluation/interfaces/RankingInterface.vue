<template>
  <div class="ranking-interface" ref="containerRef">
    <!-- Left Panel: Features with Drag & Drop Buckets -->
    <div class="left-panel" :style="leftPanelStyle()">
      <!-- Panel Header (hidden when embedded in EvaluationSession) -->
      <div v-if="!hideNavigation" class="panel-header">
        <LIcon size="20" class="mr-2">mdi-podium</LIcon>
        <h3>{{ $t('ranker.detail.featuresTitle') }}</h3>
        <v-spacer />
        <LEvaluationStatus
          :status="currentItemStatus"
          :saving="saving"
        />
      </div>

      <!-- Loading State -->
      <div v-if="loadingItem" class="loading-state">
        <v-progress-circular indeterminate color="primary" size="32" />
      </div>

      <!-- Features Panel -->
      <div
        v-else-if="groupedFeatures.length > 0"
        class="panel-content"
        :class="{ 'panel-content--readonly': !canEvaluate }"
      >
        <v-expansion-panels v-model="expandedPanels" multiple>
          <v-expansion-panel v-for="feature in groupedFeatures" :key="feature.type">
            <v-expansion-panel-title>
              <div class="feature-type-title">
                <span>{{ translateFeatureType(feature.type) }}</span>
                <LTag v-if="getFeatureProgress(feature)" variant="info" size="sm" class="ml-2">
                  {{ getFeatureProgress(feature) }}
                </LTag>
              </div>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <!-- Dynamic Buckets Container -->
              <div class="buckets-row">
                <div
                  v-for="(bucket, bIdx) in bucketConfig"
                  :key="bucket.id"
                  class="bucket"
                  :style="bucketStyle(bucket.color)"
                >
                  <h4 :style="{ color: bucket.color }">{{ bucketLabel(bucket) }}</h4>
                  <draggable
                    v-model="feature.bucketLists[bIdx]"
                    class="bucket-content"
                    :group="'featureGroup-' + feature.type"
                    item-key="feature_id"
                    :disabled="!canEvaluate"
                    @end="handleRankingChanged"
                  >
                    <template #item="{ element }">
                      <div class="bucket-item" :class="{ 'bucket-item--readonly': !canEvaluate }">
                        <div
                          class="bucket-item__text"
                          :class="{ 'bucket-item__text--clamped': element.minimized && isLongContent(element.content) }"
                          v-html="formatFeatureContent(feature.type, element.content)"
                        ></div>
                        <div v-if="isLongContent(element.content)" class="bucket-item__actions">
                          <LBtn
                            variant="tonal"
                            size="small"
                            class="toggle-more-btn"
                            :prepend-icon="element.minimized ? 'mdi-chevron-down' : 'mdi-chevron-up'"
                            @mousedown.stop
                            @touchstart.stop
                            @click.stop="toggleMinimize(element)"
                          >
                            {{ element.minimized ? $t('common.more') : $t('common.less') }}
                          </LBtn>
                        </div>
                      </div>
                    </template>
                  </draggable>
                </div>
              </div>

              <!-- Neutral Bucket (unranked items) -->
              <div class="neutral-bucket">
                <h4>{{ $t('ranker.detail.buckets.neutral') }}</h4>
                <draggable
                  v-model="feature.neutralList"
                  class="neutral-content"
                  :group="'featureGroup-' + feature.type"
                  item-key="feature_id"
                  :disabled="!canEvaluate"
                  @end="handleRankingChanged"
                >
                  <template #item="{ element }">
                    <div class="bucket-item" :class="{ 'bucket-item--readonly': !canEvaluate }">
                      <div
                        class="bucket-item__text"
                        :class="{ 'bucket-item__text--clamped': element.minimized && isLongContent(element.content) }"
                        v-html="formatFeatureContent(feature.type, element.content)"
                      ></div>
                      <div v-if="isLongContent(element.content)" class="bucket-item__actions">
                        <LBtn
                          variant="tonal"
                          size="small"
                          class="toggle-more-btn"
                          :prepend-icon="element.minimized ? 'mdi-chevron-down' : 'mdi-chevron-up'"
                          @mousedown.stop
                          @touchstart.stop
                          @click.stop="toggleMinimize(element)"
                        >
                          {{ element.minimized ? $t('common.more') : $t('common.less') }}
                        </LBtn>
                      </div>
                    </div>
                  </template>
                </draggable>
              </div>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </div>

      <!-- Empty State -->
      <div v-else class="empty-state">
        <LIcon size="48" color="grey-lighten-1">mdi-sort-variant-off</LIcon>
        <h3>{{ $t('evaluation.ranking.emptyTitle') }}</h3>
        <p>{{ $t('evaluation.ranking.noFeatures') }}</p>
      </div>

      <!-- Navigation Footer (only shown if hideNavigation is false) -->
      <div class="nav-footer" v-if="items.length > 0 && !hideNavigation">
        <LBtn
          variant="tonal"
          size="small"
          :disabled="!hasPrev"
          @click="goPrev"
        >
          <LIcon start>mdi-chevron-left</LIcon>
          {{ $t('common.previous') }}
        </LBtn>
        <span class="nav-position">
          {{ currentItemIndex + 1 }} / {{ items.length }}
        </span>
        <LBtn
          variant="primary"
          size="small"
          :disabled="!hasNext"
          @click="goNext"
        >
          {{ $t('common.next') }}
          <LIcon end>mdi-chevron-right</LIcon>
        </LBtn>
      </div>
    </div>

    <!-- Resize Handle -->
    <div class="resize-handle" @mousedown="startResize">
      <div class="handle-line" />
    </div>

    <!-- Right Panel: Email/Message Content -->
    <div class="right-panel" :style="rightPanelStyle()">
      <!-- Panel Header (hidden when embedded in EvaluationSession) -->
      <div v-if="!hideNavigation" class="panel-header">
        <LIcon size="20" class="mr-2">mdi-email-outline</LIcon>
        <h3>{{ $t('ranker.detail.emailHistory') }}</h3>
      </div>

      <div class="panel-content">
        <div v-if="loadingItem" class="loading-state">
          <v-progress-circular indeterminate color="primary" size="32" />
        </div>
        <LMessageList v-else-if="messages.length > 0" :messages="messages" />
        <div v-else-if="content" class="content-text">{{ content }}</div>
        <div v-else class="empty-state">
          <LIcon size="48" color="grey-lighten-1">mdi-text-box-off-outline</LIcon>
          <p>{{ $t('evaluation.ranking.noContent') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * RankingInterface.vue - Feature-Based Drag & Drop Ranking Interface
 *
 * Provides the UI for ranking evaluation where users sort features
 * into configurable buckets. Supports dynamic N-bucket configs from
 * props.config (e.g. 3 or 5 buckets) with legacy 3-bucket fallback.
 */
import { ref, computed, watch, onMounted, toRef } from 'vue'
import { useI18n } from 'vue-i18n'
import draggable from 'vuedraggable'
import axios from 'axios'
import { usePanelResize } from '@/composables/usePanelResize'
import { useMobile } from '@/composables/useMobile'

const props = defineProps({
  scenarioId: {
    type: [Number, String],
    required: true
  },
  scenario: {
    type: Object,
    default: null
  },
  config: {
    type: Object,
    default: () => ({})
  },
  initialItemId: {
    type: [Number, String],
    default: null
  },
  hideNavigation: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['item-completed', 'all-completed', 'status-change', 'saving-change'])

// Computed prop for hideNavigation to use in template
const hideNavigation = computed(() => props.hideNavigation)
const canEvaluate = computed(() => props.scenario?.can_evaluate !== false)

const { t, locale } = useI18n()

// Localize a value that may be a plain string or a localized object {de, en}.
// api_v1-created scenarios store bucket labels as localized objects (canonical
// evaluation_data_schemas shape); legacy scenarios store strings or {de,en}
// under `name`.
function localize(v) {
  if (v == null) return ''
  if (typeof v === 'string') return v
  return v[locale.value] || v.de || v.en || ''
}

// isMobile (<600px) lowers the "more/less" expand threshold so the toggle
// appears (and the actions row stays reachable) on narrow viewports where
// even shorter content overflows the stacked single-column buckets.
const { isMobile } = useMobile()

// Panel resize composable
const { containerRef, leftPanelStyle, rightPanelStyle, startResize } = usePanelResize({
  initialLeftPercent: 60,
  minLeftPercent: 40,
  maxLeftPercent: 75,
  storageKey: 'llars-ranking-panel-width'
})

// --- Dynamic bucket config from props.config ---
const LEGACY_BUCKETS = [
  { id: 1, name: { de: 'Gut', en: 'Good' }, color: '#98d4bb' },
  { id: 2, name: { de: 'Mittel', en: 'Medium' }, color: '#D1BC8A' },
  { id: 3, name: { de: 'Schlecht', en: 'Poor' }, color: '#e8a087' }
]

const bucketConfig = computed(() => {
  const cfg = props.config || {}
  // Read defensively across all known nestings. api_v1 scenarios wrap the
  // config under `config` (canonical evaluation_data_schemas shape); wizard
  // scenarios use `eval_config[.config]`; manual scenarios pass it flat.
  const buckets = cfg.buckets
    || cfg.config?.buckets
    || cfg.eval_config?.buckets
    || cfg.eval_config?.config?.buckets

  if (buckets && buckets.length >= 2) return buckets
  return LEGACY_BUCKETS
})

function bucketStyle(color) {
  return {
    backgroundColor: `${color}19`,
    border: `2px solid ${color}66`
  }
}

function bucketLabel(bucket) {
  // Schema buckets expose `label` ({de,en}); legacy buckets expose `name`
  // (string or {de,en}). Fall back to the id so the column is never blank.
  return localize(bucket.label) || localize(bucket.name) || bucket.id || `Bucket ${bucket.id}`
}

function normalizeBucketKey(value) {
  if (value === null || value === undefined) return ''
  return String(value)
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[\s_-]+/g, '')
}

function resolveBucketIndex(rawBucketValue) {
  const rawKey = normalizeBucketKey(rawBucketValue)
  if (!rawKey) return -1

  const cfg = bucketConfig.value
  for (let i = 0; i < cfg.length; i += 1) {
    const bucket = cfg[i]
    const candidates = [
      bucket?.id,
      bucket?.name,
      bucket?.name?.de,
      bucket?.name?.en,
      bucket?.label,
      bucket?.label?.de,
      bucket?.label?.en,
      bucket?.label_de,
      bucket?.label_en
    ]

    const hasMatch = candidates.some(candidate => normalizeBucketKey(candidate) === rawKey)
    if (hasMatch) {
      return i
    }
  }

  return -1
}

function getBucketStorageValue(bucket) {
  if (bucket && typeof bucket.id === 'string' && bucket.id.trim()) {
    return bucket.id
  }
  return bucket?.name?.de || bucket?.name?.en || bucket?.name
    || bucket?.label?.de || bucket?.label?.en || String(bucket?.id ?? '')
}

// State
const items = ref([])
const currentItem = ref(null)
const currentItemIndex = ref(0)
const messages = ref([])
const content = ref('')
const features = ref([])
const groupedFeatures = ref([])
const expandedPanels = ref([0]) // First panel expanded by default
const ranked = ref(false)

// Loading states
const loading = ref(false)
const loadingItem = ref(false)
const saving = ref(false)
const error = ref(null)

// Save queue for auto-save
const saveQueue = []
let isProcessingSaveQueue = false

// Per-case timing: when each thread was shown (thread_id → epoch ms). Sent as a
// query param with the ranking save so exports carry time-on-case; the save
// payload is a list, so timing can't ride in the body. Backend first-write-only.
const shownAtByThread = {}

// Computed
const hasNext = computed(() => currentItemIndex.value < items.value.length - 1)
const hasPrev = computed(() => currentItemIndex.value > 0)

const currentItemStatus = computed(() => {
  if (!currentItem.value) return 'pending'
  if (ranked.value) return 'done'

  const hasRankedFeatures = groupedFeatures.value.some(
    g => g.bucketLists.some(list => list.length > 0)
  )
  return hasRankedFeatures ? 'in_progress' : 'pending'
})

const progress = computed(() => {
  const total = items.value.length
  const completed = items.value.filter(item => item.evaluated || item.ranked).length
  return { total, completed }
})

// Emit status changes to parent
watch(currentItemStatus, (newStatus) => {
  emit('status-change', newStatus)
}, { immediate: true })

// Emit saving changes to parent
watch(saving, (isSaving) => {
  emit('saving-change', isSaving)
})

// Feature type translation
function translateFeatureType(type) {
  const typeMap = {
    'Zusammenfassung': t('ranker.featureTypes.summary', 'Zusammenfassung'),
    'Analyse': t('ranker.featureTypes.analysis', 'Analyse'),
    'Bewertung': t('ranker.featureTypes.evaluation', 'Bewertung'),
    'Empfehlung': t('ranker.featureTypes.recommendation', 'Empfehlung'),
    // Generated ranking features carry the technical type 'candidate' (e.g. the
    // IJCAI ranking set). Map it to a localized generic label so the accordion
    // header doesn't show the raw English token.
    'candidate': t('ranker.featureTypes.candidate', 'Antwort')
  }
  return typeMap[type] || type
}

// Format feature content (sanitize HTML if needed)
function formatFeatureContent(type, content) {
  if (!content) return ''
  return content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
}

// Check if content is long enough to show toggle.
// Mobile uses a lower threshold (~120 chars) so the expand toggle stays
// available when the clamped text would otherwise hide the rest off-screen.
const CONTENT_EXPAND_THRESHOLD = 220
const CONTENT_EXPAND_THRESHOLD_MOBILE = 120

function isLongContent(content) {
  if (!content) return false
  const threshold = isMobile.value ? CONTENT_EXPAND_THRESHOLD_MOBILE : CONTENT_EXPAND_THRESHOLD
  return content.length > threshold
}

// Toggle minimize state
function toggleMinimize(element) {
  element.minimized = !element.minimized
}

// Get progress for a feature group
function getFeatureProgress(feature) {
  const rankedCount = feature.bucketLists.reduce((acc, list) => acc + list.length, 0)
  const total = rankedCount + feature.neutralList.length
  if (total === 0) return null
  return `${rankedCount}/${total}`
}

// Group features by type — creates dynamic bucketLists array
function groupFeaturesByType(featureList) {
  const featureMap = new Map()
  const numBuckets = bucketConfig.value.length

  featureList.forEach((f, index) => {
    const type = f.type || 'Allgemein'
    if (!featureMap.has(type)) {
      featureMap.set(type, {
        type,
        bucketLists: Array.from({ length: numBuckets }, () => []),
        neutralList: []
      })
    }

    featureMap.get(type).neutralList.push({
      model_name: f.model_name,
      content: f.content,
      feature_id: f.feature_id || f.id || `feature-${index}`,
      position: index,
      minimized: true
    })
  })

  return featureMap
}

// Apply server ranking to feature map (new format: details array with bucket field)
function applyServerRanking(featureMap, serverRanking) {
  if (!serverRanking || !Array.isArray(serverRanking)) return featureMap

  serverRanking.forEach(serverGroup => {
    if (featureMap.has(serverGroup.type)) {
      const group = featureMap.get(serverGroup.type)
      const numBuckets = bucketConfig.value.length

      // Collect all features
      const allFeatures = [
        ...group.bucketLists.flat(),
        ...group.neutralList
      ]

      // Reset lists
      group.bucketLists = Array.from({ length: numBuckets }, () => [])
      group.neutralList = []

      // Apply server ranking using details array
      if (serverGroup.details && Array.isArray(serverGroup.details)) {
        serverGroup.details.forEach(detail => {
          const feature = allFeatures.find(f =>
            f.feature_id === detail.feature_id ||
            f.content === detail.content
          ) || {
            ...detail,
            minimized: true
          }

          // Map server bucket robustly (id/de/en/normalized aliases)
          const bIdx = resolveBucketIndex(detail.bucket)
          if (bIdx >= 0) {
            group.bucketLists[bIdx].push(feature)
          } else {
            group.neutralList.push(feature)
          }
        })
      }

      // Put remaining unranked features in neutral
      allFeatures.forEach(f => {
        const isPlaced =
          group.bucketLists.some(list => list.some(g => g.feature_id === f.feature_id)) ||
          group.neutralList.some(g => g.feature_id === f.feature_id)

        if (!isPlaced) {
          group.neutralList.push(f)
        }
      })
    }
  })

  return featureMap
}

// Prepare features for server save (includes feature_id for reliable lookup)
function prepareForServerSave() {
  return groupedFeatures.value.map(group => ({
    type: group.type,
    details: group.bucketLists.flatMap((list, bIdx) =>
      list.map((detail, position) => ({
        feature_id: detail.feature_id,
        model_name: detail.model_name,
        content: detail.content,
        position,
        bucket: getBucketStorageValue(bucketConfig.value[bIdx])
      }))
    )
  }))
}

// Check if fully ranked
function isFullyRanked() {
  const total = features.value.length
  if (total === 0) return false

  const rankedCount = groupedFeatures.value.reduce((acc, g) =>
    acc + g.bucketLists.reduce((sum, list) => sum + list.length, 0), 0
  )

  return rankedCount === total
}

// Deep clone helper
function deepClone(value) {
  return JSON.parse(JSON.stringify(value))
}

// Handle ranking changed (drag & drop)
function handleRankingChanged() {
  if (!canEvaluate.value) return

  const threadId = currentItem.value?.thread_id
  if (!threadId) return

  saveToLocalStorage(threadId)

  const orderedFeatures = deepClone(prepareForServerSave())
  enqueueAutoSave(threadId, orderedFeatures)
}

// Save bucket assignments to localStorage (uses bucket index)
function saveToLocalStorage(threadId) {
  const key = `ranking_buckets_${threadId}`
  const bucketAssignments = {}

  groupedFeatures.value.forEach(group => {
    group.bucketLists.forEach((list, bIdx) => {
      list.forEach((f, idx) => {
        bucketAssignments[f.feature_id] = { bucket: bIdx, position: idx }
      })
    })
  })

  localStorage.setItem(key, JSON.stringify(bucketAssignments))
}

// Enqueue auto-save
function enqueueAutoSave(threadId, payload) {
  if (!threadId) return

  const existingIndex = saveQueue.findIndex(t => t.threadId === threadId)
  const task = { threadId, payload }

  if (existingIndex !== -1) {
    saveQueue[existingIndex] = task
  } else {
    saveQueue.push(task)
  }

  void processSaveQueue()
}

// Process save queue
async function processSaveQueue() {
  if (isProcessingSaveQueue) return
  isProcessingSaveQueue = true

  try {
    while (saveQueue.length > 0) {
      const task = saveQueue.shift()
      saving.value = true

      try {
        // Timing + scenario as query params (the body is a bucket list, not an
        // object, so they can't be body keys).
        const shownAt = shownAtByThread[task.threadId]
        const params = new URLSearchParams({ scenario_id: String(props.scenarioId) })
        if (shownAt) params.set('time_on_item_ms', String(Date.now() - shownAt))
        await axios.post(
          `/api/save_ranking/${task.threadId}?${params.toString()}`,
          task.payload,
          { headers: { 'Content-Type': 'application/json' } }
        )

        // Update ranked status
        if (currentItem.value?.thread_id === task.threadId) {
          ranked.value = isFullyRanked()

          if (ranked.value) {
            emit('item-completed', task.threadId)

            const itemIndex = items.value.findIndex(
              item => (item.thread_id || item.id) === task.threadId
            )
            if (itemIndex >= 0) {
              items.value[itemIndex].ranked = true
              items.value[itemIndex].evaluated = true
            }

            if (progress.value.completed === progress.value.total) {
              emit('all-completed')
            }
          }
        }
      } catch (err) {
        console.error('Failed to save ranking:', err)
        saveQueue.unshift(task)
        break
      } finally {
        saving.value = false
      }
    }
  } finally {
    saving.value = false
    isProcessingSaveQueue = false
  }
}

// Load items
async function loadItems() {
  loading.value = true
  error.value = null

  try {
    const response = await axios.get(`/api/evaluation/session/${props.scenarioId}`)
    items.value = response.data.items || []

    if (items.value.length > 0) {
      let targetThreadId = null

      if (props.initialItemId) {
        const initialId = Number(props.initialItemId)
        const targetItem = items.value.find(item =>
          (item.thread_id || item.id || item.item_id) === initialId
        )
        if (targetItem) {
          targetThreadId = targetItem.thread_id || targetItem.id || targetItem.item_id
        }
      }

      if (!targetThreadId) {
        const firstItem = items.value[0]
        targetThreadId = firstItem.thread_id || firstItem.id || firstItem.item_id
      }

      await loadItem(targetThreadId)
    }
  } catch (err) {
    console.error('Failed to load items:', err)
    error.value = err.response?.data?.error || 'Failed to load items'
  } finally {
    loading.value = false
  }
}

// Load a specific item
async function loadItem(threadId) {
  loadingItem.value = true
  error.value = null

  try {
    const response = await axios.get(`/api/email_threads/rankings/${threadId}`)

    currentItem.value = {
      thread_id: threadId,
      chat_id: response.data.chat_id,
      subject: response.data.subject,
      ranked: response.data.ranked
    }
    // Start the per-case timer when this thread becomes visible (keep the first
    // shown time if the rater revisits — mirrors the backend first-write rule).
    if (!shownAtByThread[threadId]) shownAtByThread[threadId] = Date.now()
    messages.value = response.data.messages || []
    content.value = response.data.content || response.data.reference_content || ''
    features.value = response.data.features || []
    ranked.value = response.data.ranked || false

    // Group features by type
    const featureMap = groupFeaturesByType(features.value)

    // Try to load existing ranking from server
    try {
      const rankingResponse = await axios.get(`/api/email_threads/${threadId}/current_ranking`)
      if (rankingResponse.data && rankingResponse.data.length > 0) {
        applyServerRanking(featureMap, rankingResponse.data)
      }
    } catch {
      // No existing ranking - check localStorage
      applyLocalStorageBuckets(featureMap, threadId)
    }

    groupedFeatures.value = Array.from(featureMap.values())

    // Expand first panel by default
    expandedPanels.value = groupedFeatures.value.length > 0 ? [0] : []

    // Update current index
    const index = items.value.findIndex(item =>
      (item.thread_id || item.id || item.item_id) === threadId
    )
    if (index >= 0) {
      currentItemIndex.value = index
    }
  } catch (err) {
    console.error('Failed to load item:', err)
    error.value = err.response?.data?.error || 'Failed to load item'
  } finally {
    loadingItem.value = false
  }
}

// Apply localStorage bucket assignments (uses bucket index)
function applyLocalStorageBuckets(featureMap, threadId) {
  const key = `ranking_buckets_${threadId}`
  const savedData = localStorage.getItem(key)

  if (!savedData) return

  try {
    const bucketAssignments = JSON.parse(savedData)
    const numBuckets = bucketConfig.value.length

    featureMap.forEach((group) => {
      const allFeatures = [...group.neutralList]
      group.bucketLists = Array.from({ length: numBuckets }, () => [])
      group.neutralList = []

      allFeatures.forEach(feature => {
        const assignment = bucketAssignments[feature.feature_id]
        if (assignment && typeof assignment.bucket === 'number' && assignment.bucket < numBuckets) {
          group.bucketLists[assignment.bucket].push({ ...feature, position: assignment.position })
        } else {
          group.neutralList.push(feature)
        }
      })

      // Sort each bucket by position
      group.bucketLists.forEach(list => {
        list.sort((a, b) => (a.position || 0) - (b.position || 0))
      })
    })
  } catch (e) {
    console.warn('Failed to parse localStorage bucket assignments:', e)
  }
}

// Navigation
async function goToItem(index) {
  if (index >= 0 && index < items.value.length) {
    const item = items.value[index]
    const threadId = item.thread_id || item.id || item.item_id
    await loadItem(threadId)
  }
}

async function goNext() {
  if (hasNext.value) {
    await goToItem(currentItemIndex.value + 1)
  }
}

async function goPrev() {
  if (hasPrev.value) {
    await goToItem(currentItemIndex.value - 1)
  }
}

// Initialize on mount
onMounted(async () => {
  await loadItems()
  if (props.initialItemId && items.value.length > 0) {
    const targetId = Number(props.initialItemId)
    const targetIndex = items.value.findIndex(item =>
      (item.thread_id || item.id || item.item_id) === targetId
    )
    if (targetIndex >= 0 && targetIndex !== currentItemIndex.value) {
      const item = items.value[targetIndex]
      await loadItem(item.thread_id || item.id || item.item_id)
    }
  }
})

// Watch for scenario changes
watch(() => props.scenarioId, (newId) => {
  if (newId) {
    loadItems()
  }
})

// Watch for initialItemId changes (navigation between items)
watch(() => props.initialItemId, (newItemId) => {
  if (newItemId && items.value.length > 0) {
    const targetId = Number(newItemId)
    const currentId = currentItem.value?.thread_id || currentItem.value?.id || currentItem.value?.item_id
    if (currentId === targetId) return

    const targetItem = items.value.find(item =>
      (item.thread_id || item.id || item.item_id) === targetId
    )
    if (targetItem) {
      const threadId = targetItem.thread_id || targetItem.id || targetItem.item_id
      loadItem(threadId)
    }
  }
})
</script>

<style scoped>
.ranking-interface {
  display: flex;
  height: 100%;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
}

/* Panels */
.left-panel,
.right-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.left-panel {
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.panel-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.3);
  flex-shrink: 0;
}

.panel-header h3 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* Resize Handle */
.resize-handle {
  width: 6px;
  cursor: col-resize;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  flex-shrink: 0;
}

.resize-handle:hover {
  background: rgba(var(--v-theme-primary), 0.15);
}

.handle-line {
  width: 3px;
  height: 40px;
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 2px;
}

/* Loading & Empty States */
.loading-state,
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  min-height: 200px;
}

.content-text {
  white-space: pre-wrap;
  line-height: 1.6;
}

/* Feature Type Title */
.feature-type-title {
  display: flex;
  align-items: center;
}

/* Buckets */
.buckets-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.bucket {
  flex: 1;
  min-height: 150px;
  padding: 12px;
  border-radius: 12px 3px 12px 3px;
  display: flex;
  flex-direction: column;
}

.bucket h4 {
  margin: 0 0 8px 0;
  font-size: 0.875rem;
  font-weight: 600;
}

.bucket-content {
  flex: 1;
  min-height: 80px;
  /* Long item lists scroll inside the bucket instead of overflowing off the
     viewport (critical on mobile where buckets stack and height is scarce). */
  max-height: inherit;
  overflow-y: auto;
}

.panel-content--readonly .bucket,
.panel-content--readonly .neutral-bucket {
  opacity: 0.6;
}

/* Neutral Bucket */
.neutral-bucket {
  background-color: rgba(var(--v-theme-surface-variant), 0.5);
  border: 2px dashed rgba(var(--v-theme-on-surface), 0.2);
  padding: 12px;
  border-radius: 12px 3px 12px 3px;
  margin-top: 8px;
}

.neutral-bucket h4 {
  margin: 0 0 8px 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.neutral-content {
  min-height: 60px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* Bucket Items */
.bucket-item {
  background-color: rgb(var(--v-theme-surface));
  border-radius: 8px 3px 8px 3px;
  padding: 12px;
  margin-bottom: 8px;
  cursor: grab;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  position: relative;
  font-size: 0.875rem;
  line-height: 1.5;
  transition: all 0.2s ease;
}

.bucket-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
}

.bucket-item:active {
  cursor: grabbing;
}

.bucket-item--readonly {
  cursor: default;
}

.bucket-item--readonly:active {
  cursor: default;
}

.bucket-item--readonly:hover {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  transform: none;
}

.bucket-item__text {
  word-break: break-word;
}

.bucket-item__text--clamped {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.bucket-item__actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.toggle-more-btn {
  min-height: 24px !important;
  padding: 3px 9px !important;
  font-size: 0.72rem;
  border-radius: 12px 3px 12px 3px;
  color: rgb(var(--v-theme-primary));
  border: 1px solid rgba(var(--v-theme-primary), 0.25);
  background: rgba(var(--v-theme-primary), 0.08);
}

.toggle-more-btn:hover:not(:disabled) {
  background: rgba(var(--v-theme-primary), 0.16);
  border-color: rgba(var(--v-theme-primary), 0.35);
  transform: none;
}

/* Drag & Drop States */
.sortable-ghost {
  opacity: 0.4;
}

.sortable-chosen {
  background-color: rgba(var(--v-theme-primary), 0.15);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Navigation Footer */
.nav-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.3);
  flex-shrink: 0;
  gap: 12px;
}

.nav-footer .nav-position {
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  min-width: 60px;
  text-align: center;
}

/* Responsive */

/* Intermediate breakpoint: with 5+ buckets the flex row compresses each
   bucket below a usable width. Allowing wrap (and giving each bucket a sane
   min-width) keeps buckets readable by flowing them onto multiple lines
   instead of squeezing them all into one. Desktop (>1024px) is untouched. */
@media (max-width: 1024px) {
  .buckets-row {
    flex-wrap: wrap;
  }

  .buckets-row .bucket {
    flex: 1 1 160px;
    min-width: 140px;
  }
}

/* Small tablets (600–905px): stack panels but keep them roomier than phones.
   Left panel ~50vh, right panel splits evenly; buckets shrink a bit. */
@media (max-width: 905px) and (min-width: 601px) {
  .ranking-interface {
    flex-direction: column;
  }

  .left-panel,
  .right-panel {
    width: 100% !important;
  }

  .left-panel {
    max-height: 50vh;
    border-right: none;
    border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  }

  .right-panel {
    max-height: 50vh;
  }

  .resize-handle {
    display: none;
  }

  .bucket {
    min-height: 60px;
  }
}

@media (max-width: 768px) {
  .ranking-interface {
    flex-direction: column;
  }

  .left-panel,
  .right-panel {
    width: 100% !important;
  }

  .left-panel {
    max-height: 60vh;
    border-right: none;
    border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  }

  .right-panel {
    max-height: 40vh;
  }

  .resize-handle {
    display: none;
  }

  .buckets-row {
    flex-direction: column;
    gap: 8px;
  }

  .bucket {
    min-height: 100px;
  }
}

/* Phone (<=600px) — the weakest viewport for this interface.
   Mirrors the ComparisonInterface mobile patterns (thin chrome, compact
   headers, >=38px tap targets). Stacks buckets fully, shrinks fonts,
   compresses padding, and fixes touch targets. */
@media (max-width: 600px) {
  /* Tighter content padding (16px -> 12px) to reclaim horizontal room. */
  .panel-content {
    padding: 12px;
  }

  .panel-header {
    padding: 8px 12px;
  }

  .panel-header h3 {
    font-size: 0.85rem;
  }

  /* Buckets stack to a single column; tighter gap (12px -> 8px). */
  .buckets-row {
    flex-direction: column;
    flex-wrap: nowrap;
    gap: 8px;
  }

  /* Shorter buckets so several fit without endless scrolling; the
     bucket-content scroll rule keeps long lists contained. */
  .buckets-row .bucket {
    flex: 1 1 auto;
    min-width: 0;
    min-height: 60px;
    padding: 8px;
  }

  .bucket h4,
  .neutral-bucket h4 {
    font-size: 0.78rem;
    margin-bottom: 6px;
  }

  .neutral-bucket {
    padding: 8px;
  }

  /* Compact item cards: smaller font (0.875 -> 0.78rem) + tighter padding. */
  .bucket-item {
    font-size: 0.78rem;
    padding: 8px;
    margin-bottom: 6px;
  }

  /* "more/less" toggle: meet touch-target + readability minimums. */
  .toggle-more-btn {
    min-height: 38px !important;
    padding: 8px 12px !important;
    font-size: 0.8rem;
  }

  /* Navigation footer buttons need a >=38px tap target on a phone. */
  .nav-footer {
    padding: 8px 12px;
    gap: 8px;
  }

  .nav-footer :deep(.v-btn) {
    min-height: 38px;
  }
}
</style>
