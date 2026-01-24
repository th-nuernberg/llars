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
      <div v-else-if="groupedFeatures.length > 0" class="panel-content">
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
              <!-- Buckets Container -->
              <div class="buckets-row">
                <!-- Good Bucket -->
                <div class="bucket good-bucket">
                  <h4>{{ $t('ranker.detail.buckets.good') }}</h4>
                  <draggable
                    v-model="feature.goodList"
                    class="bucket-content"
                    :group="'featureGroup-' + feature.type"
                    item-key="feature_id"
                    @end="handleRankingChanged"
                  >
                    <template #item="{ element }">
                      <div class="bucket-item">
                        <div v-html="formatFeatureContent(feature.type, element.content)"></div>
                      </div>
                    </template>
                  </draggable>
                </div>

                <!-- Moderate Bucket -->
                <div class="bucket moderate-bucket">
                  <h4>{{ $t('ranker.detail.buckets.average') }}</h4>
                  <draggable
                    v-model="feature.averageList"
                    class="bucket-content"
                    :group="'featureGroup-' + feature.type"
                    item-key="feature_id"
                    @end="handleRankingChanged"
                  >
                    <template #item="{ element }">
                      <div class="bucket-item">
                        <div v-html="formatFeatureContent(feature.type, element.content)"></div>
                      </div>
                    </template>
                  </draggable>
                </div>

                <!-- Bad Bucket -->
                <div class="bucket bad-bucket">
                  <h4>{{ $t('ranker.detail.buckets.bad') }}</h4>
                  <draggable
                    v-model="feature.badList"
                    class="bucket-content"
                    :group="'featureGroup-' + feature.type"
                    item-key="feature_id"
                    @end="handleRankingChanged"
                  >
                    <template #item="{ element }">
                      <div class="bucket-item">
                        <div v-html="formatFeatureContent(feature.type, element.content)"></div>
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
                  @end="handleRankingChanged"
                >
                  <template #item="{ element }">
                    <div class="bucket-item">
                      <div :class="{ 'clamped-text': element.minimized }" v-html="formatFeatureContent(feature.type, element.content)"></div>
                      <v-btn
                        v-if="isLongContent(element.content)"
                        size="x-small"
                        variant="text"
                        class="toggle-btn"
                        @click.stop="toggleMinimize(element)"
                      >
                        {{ element.minimized ? $t('common.more') : $t('common.less') }}
                      </v-btn>
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
 * (e.g., summaries, analyses) into predefined buckets (Good, Moderate, Bad).
 * Features can be dragged between buckets using vuedraggable.
 */
import { ref, computed, watch, onMounted, toRef } from 'vue'
import { useI18n } from 'vue-i18n'
import draggable from 'vuedraggable'
import axios from 'axios'
import { usePanelResize } from '@/composables/usePanelResize'

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

const { t } = useI18n()

// Panel resize composable
const { containerRef, leftPanelStyle, rightPanelStyle, startResize } = usePanelResize({
  initialLeftPercent: 60,
  minLeftPercent: 40,
  maxLeftPercent: 75,
  storageKey: 'llars-ranking-panel-width'
})

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

// Computed
const hasNext = computed(() => currentItemIndex.value < items.value.length - 1)
const hasPrev = computed(() => currentItemIndex.value > 0)

const currentItemStatus = computed(() => {
  if (!currentItem.value) return 'pending'
  if (ranked.value) return 'done'

  // Check if any features are ranked
  const hasRankedFeatures = groupedFeatures.value.some(
    g => g.goodList.length > 0 || g.averageList.length > 0 || g.badList.length > 0
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
    'Empfehlung': t('ranker.featureTypes.recommendation', 'Empfehlung')
  }
  return typeMap[type] || type
}

// Format feature content (sanitize HTML if needed)
function formatFeatureContent(type, content) {
  if (!content) return ''
  // Basic HTML escaping for safety
  return content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
}

// Check if content is long enough to show toggle
function isLongContent(content) {
  return content && content.length > 200
}

// Toggle minimize state
function toggleMinimize(element) {
  element.minimized = !element.minimized
}

// Get progress for a feature group
function getFeatureProgress(feature) {
  const total = feature.goodList.length + feature.averageList.length +
                feature.badList.length + feature.neutralList.length
  const ranked = feature.goodList.length + feature.averageList.length + feature.badList.length
  if (total === 0) return null
  return `${ranked}/${total}`
}

// Group features by type
function groupFeaturesByType(featureList) {
  const featureMap = new Map()

  featureList.forEach((f, index) => {
    const type = f.type || 'Allgemein'
    if (!featureMap.has(type)) {
      featureMap.set(type, {
        type,
        goodList: [],
        averageList: [],
        badList: [],
        neutralList: []
      })
    }

    // Place feature initially in neutral list
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

// Apply server ranking to feature map
function applyServerRanking(featureMap, serverRanking) {
  if (!serverRanking || !Array.isArray(serverRanking)) return featureMap

  serverRanking.forEach(serverGroup => {
    if (featureMap.has(serverGroup.type)) {
      const group = featureMap.get(serverGroup.type)

      // Clear existing lists
      const allFeatures = [
        ...group.goodList,
        ...group.averageList,
        ...group.badList,
        ...group.neutralList
      ]

      group.goodList = []
      group.averageList = []
      group.badList = []
      group.neutralList = []

      // Apply server ranking
      if (serverGroup.details && Array.isArray(serverGroup.details)) {
        serverGroup.details.forEach(detail => {
          const feature = allFeatures.find(f =>
            f.feature_id === detail.feature_id ||
            f.content === detail.content
          ) || {
            ...detail,
            minimized: true
          }

          if (detail.bucket === 'Gut') {
            group.goodList.push(feature)
          } else if (detail.bucket === 'Mittel') {
            group.averageList.push(feature)
          } else if (detail.bucket === 'Schlecht') {
            group.badList.push(feature)
          } else {
            group.neutralList.push(feature)
          }
        })
      }

      // Put remaining unranked features in neutral
      allFeatures.forEach(f => {
        const isRanked =
          group.goodList.some(g => g.feature_id === f.feature_id) ||
          group.averageList.some(g => g.feature_id === f.feature_id) ||
          group.badList.some(g => g.feature_id === f.feature_id) ||
          group.neutralList.some(g => g.feature_id === f.feature_id)

        if (!isRanked) {
          group.neutralList.push(f)
        }
      })
    }
  })

  return featureMap
}

// Prepare features for server save
function prepareForServerSave() {
  return groupedFeatures.value.map(group => ({
    type: group.type,
    details: [
      ...group.goodList.map((detail, index) => ({
        model_name: detail.model_name,
        content: detail.content,
        position: index,
        bucket: 'Gut'
      })),
      ...group.averageList.map((detail, index) => ({
        model_name: detail.model_name,
        content: detail.content,
        position: index,
        bucket: 'Mittel'
      })),
      ...group.badList.map((detail, index) => ({
        model_name: detail.model_name,
        content: detail.content,
        position: index,
        bucket: 'Schlecht'
      }))
    ]
  }))
}

// Check if fully ranked
function isFullyRanked() {
  const total = features.value.length
  if (total === 0) return false

  const rankedCount = groupedFeatures.value.reduce((acc, g) =>
    acc + g.goodList.length + g.averageList.length + g.badList.length, 0
  )

  return rankedCount === total
}

// Deep clone helper
function deepClone(value) {
  return JSON.parse(JSON.stringify(value))
}

// Handle ranking changed (drag & drop)
function handleRankingChanged() {
  const threadId = currentItem.value?.thread_id
  if (!threadId) return

  // Save to localStorage for persistence
  saveToLocalStorage(threadId)

  // Enqueue auto-save to server
  const orderedFeatures = deepClone(prepareForServerSave())
  enqueueAutoSave(threadId, orderedFeatures)
}

// Save bucket assignments to localStorage
function saveToLocalStorage(threadId) {
  const key = `ranking_buckets_${threadId}`
  const bucketAssignments = {}

  groupedFeatures.value.forEach(group => {
    group.goodList.forEach((f, idx) => {
      bucketAssignments[f.feature_id] = { bucket: 'good', position: idx }
    })
    group.averageList.forEach((f, idx) => {
      bucketAssignments[f.feature_id] = { bucket: 'average', position: idx }
    })
    group.badList.forEach((f, idx) => {
      bucketAssignments[f.feature_id] = { bucket: 'bad', position: idx }
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
        await axios.post(
          `/api/save_ranking/${task.threadId}`,
          task.payload,
          { headers: { 'Content-Type': 'application/json' } }
        )

        // Update ranked status
        if (currentItem.value?.thread_id === task.threadId) {
          ranked.value = isFullyRanked()

          if (ranked.value) {
            emit('item-completed', task.threadId)

            // Check if all items completed
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
        saveQueue.unshift(task) // Re-add to queue on failure
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
    // Load items via evaluation session endpoint
    const response = await axios.get(`/api/evaluation/session/${props.scenarioId}`)
    items.value = response.data.items || []

    if (items.value.length > 0) {
      // Use initialItemId if provided, otherwise use first item
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

      // Fallback to first item if initialItemId not found
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
    // Load thread details with features
    const response = await axios.get(`/api/email_threads/rankings/${threadId}`)

    currentItem.value = {
      thread_id: threadId,
      chat_id: response.data.chat_id,
      subject: response.data.subject,
      ranked: response.data.ranked
    }
    messages.value = response.data.messages || []
    features.value = response.data.features || []
    ranked.value = response.data.ranked || false

    // Group features by type
    const featureMap = groupFeaturesByType(features.value)

    // Try to load existing ranking from server
    try {
      const rankingResponse = await axios.get(`/api/email_threads/${threadId}/current_ranking`)
      if (rankingResponse.data && rankingResponse.data.length > 0) {
        applyServerRanking(featureMap, rankingResponse.data)
        // Don't override ranked.value here - it was correctly set from response.data.ranked
        // which is calculated server-side via has_user_fully_ranked_thread()
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

// Apply localStorage bucket assignments
function applyLocalStorageBuckets(featureMap, threadId) {
  const key = `ranking_buckets_${threadId}`
  const savedData = localStorage.getItem(key)

  if (!savedData) return

  try {
    const bucketAssignments = JSON.parse(savedData)

    featureMap.forEach((group) => {
      const allFeatures = [...group.neutralList]
      group.goodList = []
      group.averageList = []
      group.badList = []
      group.neutralList = []

      allFeatures.forEach(feature => {
        const assignment = bucketAssignments[feature.feature_id]
        if (assignment) {
          if (assignment.bucket === 'good') {
            group.goodList.push({ ...feature, position: assignment.position })
          } else if (assignment.bucket === 'average') {
            group.averageList.push({ ...feature, position: assignment.position })
          } else if (assignment.bucket === 'bad') {
            group.badList.push({ ...feature, position: assignment.position })
          } else {
            group.neutralList.push(feature)
          }
        } else {
          group.neutralList.push(feature)
        }
      })

      // Sort by position
      group.goodList.sort((a, b) => (a.position || 0) - (b.position || 0))
      group.averageList.sort((a, b) => (a.position || 0) - (b.position || 0))
      group.badList.sort((a, b) => (a.position || 0) - (b.position || 0))
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
  // Navigate to initial item if specified
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
    // Check if this item is already the current item
    const currentId = currentItem.value?.thread_id || currentItem.value?.id || currentItem.value?.item_id
    if (currentId === targetId) return // Already on this item

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
}

/* Good Bucket - LLARS Success */
.good-bucket {
  background-color: rgba(152, 212, 187, 0.1);
  border: 2px solid rgba(152, 212, 187, 0.4);
}

.good-bucket h4 {
  color: var(--llars-success, #98d4bb);
}

/* Moderate Bucket - LLARS Secondary */
.moderate-bucket {
  background-color: rgba(209, 188, 138, 0.1);
  border: 2px solid rgba(209, 188, 138, 0.4);
}

.moderate-bucket h4 {
  color: var(--llars-secondary, #D1BC8A);
}

/* Bad Bucket - LLARS Danger */
.bad-bucket {
  background-color: rgba(232, 160, 135, 0.1);
  border: 2px solid rgba(232, 160, 135, 0.4);
}

.bad-bucket h4 {
  color: var(--llars-danger, #e8a087);
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

.clamped-text {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.toggle-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  font-size: 0.625rem;
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
</style>
