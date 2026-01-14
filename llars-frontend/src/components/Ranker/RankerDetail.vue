<template>
  <LEvaluationLayout
    :title="threadTitle"
    :subtitle="$t('ranker.detail.threadLabel', { id: currentThreadId })"
    :back-label="$t('ranker.detail.backLabel')"
    :status="evaluationStatus"
    :saving="saving"
    :can-go-prev="canGoPrev"
    :can-go-next="canGoNext"
    :current-index="currentIndex"
    :total-items="rankingThreadsList.length"
    @back="navigateBackToRanker"
    @prev="navigateToPreviousCase"
    @next="navigateToNextCase"
  >
    <!-- Main Content -->
    <div ref="containerRef" class="content-panels" :class="{ 'is-mobile': isMobile }">
      <!-- Feature-Bereich (links) -->
      <div class="panel features-panel" :style="leftPanelStyle()">
        <div class="panel-header">
          <LIcon size="20" class="mr-2">mdi-format-list-bulleted</LIcon>
          <span class="panel-title">{{ $t('ranker.detail.featuresTitle') }}</span>
        </div>
        <div class="panel-content">
          <v-expansion-panels>
            <v-expansion-panel v-for="feature in groupedFeatures" :key="feature.type">
              <v-expansion-panel-title>
                <div>{{ translateFeatureType(feature.type) }}</div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <!-- Buckets Container -->
                <div class="buckets-row">
                  <!-- Gut Bucket -->
                  <div class="bucket good-bucket">
                    <h4>{{ $t('ranker.detail.buckets.good') }}</h4>
                    <draggable
                      v-model="feature.goodList"
                      class="bucket-content"
                      group="featureGroup"
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

                  <!-- Mittel Bucket -->
                  <div class="bucket average-bucket">
                    <h4>{{ $t('ranker.detail.buckets.average') }}</h4>
                    <draggable
                      v-model="feature.averageList"
                      class="bucket-content"
                      group="featureGroup"
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

                  <!-- Schlecht Bucket -->
                  <div class="bucket bad-bucket">
                    <h4>{{ $t('ranker.detail.buckets.bad') }}</h4>
                    <draggable
                      v-model="feature.badList"
                      class="bucket-content"
                      group="featureGroup"
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
                </div>

                <!-- Neutraler Bucket -->
                <div class="neutral-bucket">
                  <h4>{{ $t('ranker.detail.buckets.neutral') }}</h4>
                  <draggable
                    v-model="feature.neutralList"
                    class="neutral-content"
                    group="featureGroup"
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
      </div>

      <!-- Resize Divider (hidden on mobile) -->
      <div
        v-if="!isMobile"
        class="resize-divider"
        :class="{ 'resizing': isResizing }"
        @mousedown="startResize"
      >
        <div class="resize-handle"></div>
      </div>

      <!-- E-Mail Verlauf (rechts, hidden on mobile) -->
      <div v-if="!isMobile" class="panel email-panel" :style="rightPanelStyle()">
        <div class="panel-header">
          <LIcon size="20" class="mr-2">mdi-email-outline</LIcon>
          <span class="panel-title">{{ $t('ranker.detail.emailHistory') }}</span>
        </div>
        <div class="panel-content">
          <LMessageList :messages="messages" />
        </div>
      </div>
    </div>
  </LEvaluationLayout>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import draggable from 'vuedraggable'
import {
  useRankerFeatures,
  useRankerApi,
  useRankerHelpers
} from './RankerDetail/composables'
import { usePanelResize } from '@/composables/usePanelResize'
import { useMobile } from '@/composables/useMobile'

const { isMobile } = useMobile()

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

// Panel Resize
const {
  isResizing,
  containerRef,
  startResize,
  leftPanelStyle,
  rightPanelStyle
} = usePanelResize({
  initialLeftPercent: 60,
  minLeftPercent: 30,
  maxLeftPercent: 80,
  storageKey: 'ranker-panel-width'
})

const {
  features,
  groupedFeatures,
  localStorageKey,
  ranked,
  saveToLocalStorage,
  loadFromLocalStorage,
  groupFeaturesByType,
  applyServerRanking,
  prepareForServerSave
} = useRankerFeatures()

const {
  fetchEmailThreads,
  fetchServerRanking,
  fetchRankingThreads,
  saveRankingToServer
} = useRankerApi()

const {
  toggleMinimize,
  isLongContent,
  translateFeatureType,
  formatFeatureContent
} = useRankerHelpers()

const messages = ref([])
const rankingThreadsList = ref([])
const threadTitle = ref(t('ranker.detail.defaultTitle'))

// Auto-save state
const saving = ref(false)
const saveErrors = ref({})
const lastSavedAt = ref({})

const currentThreadId = computed(() => (route.params.id ? String(route.params.id) : ''))

// Navigation
const currentIndex = computed(() => {
  const id = parseInt(route.params.id)
  return rankingThreadsList.value.findIndex(t => t.thread_id === id)
})
const canGoPrev = computed(() => currentIndex.value > 0)
const canGoNext = computed(() => currentIndex.value >= 0 && currentIndex.value < rankingThreadsList.value.length - 1)

// Evaluation status for LEvaluationStatus component
const evaluationStatus = computed(() => {
  if (ranked.value === null) return 'pending'
  return ranked.value ? 'done' : 'in_progress'
})

const saveQueue = []
let isProcessingSaveQueue = false

function deepClone(value) {
  return JSON.parse(JSON.stringify(value))
}

function isFullyRankedPayload(payload) {
  const total = Array.isArray(features.value) ? features.value.length : 0
  if (total <= 0) return false
  const rankedCount = Array.isArray(payload)
    ? payload.reduce((acc, g) => acc + (Array.isArray(g.details) ? g.details.length : 0), 0)
    : 0
  return rankedCount === total
}

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

async function processSaveQueue() {
  if (isProcessingSaveQueue) return
  isProcessingSaveQueue = true

  try {
    while (saveQueue.length > 0) {
      const task = saveQueue.shift()
      saving.value = true

      try {
        const result = await saveRankingToServer(task.threadId, task.payload)
        if (!result.success) {
          saveErrors.value[task.threadId] = result.error?.message || 'Fehler beim Speichern.'
          saveQueue.unshift(task)
          break
        }

        lastSavedAt.value[task.threadId] = Date.now()

        if (currentThreadId.value === task.threadId) {
          ranked.value = isFullyRankedPayload(task.payload)
        }
      } finally {
        saving.value = false
      }
    }
  } finally {
    saving.value = false
    isProcessingSaveQueue = false
  }
}

function handleRankingChanged() {
  const threadId = currentThreadId.value
  if (!threadId) return

  saveToLocalStorage(threadId)
  const orderedFeatures = deepClone(prepareForServerSave())
  enqueueAutoSave(threadId, orderedFeatures)
}

function isClientMessage(sender) {
  const normalizedSender = String(sender || '').toLowerCase().trim()
  const clientVariants = ['ratsuchende person', 'ratsuchender', 'ratsuchend', 'ratsuchende']
  return clientVariants.includes(normalizedSender)
}

const loadCaseData = async (caseId) => {
  // Lade Thread-Liste für Navigation
  const threads = await fetchRankingThreads()
  if (threads) {
    rankingThreadsList.value = threads
    const currentThread = threads.find(t => t.thread_id === parseInt(caseId))
    if (currentThread) {
      threadTitle.value = currentThread.subject || t('ranker.detail.defaultTitle')
    }
  }

  let dataLoadedFromLocalStorage = false

  if (loadFromLocalStorage(caseId)) {
    dataLoadedFromLocalStorage = true
  }

  if (!dataLoadedFromLocalStorage) {
    const threadData = await fetchEmailThreads(caseId)
    if (!threadData) return

    const serverRanking = await fetchServerRanking(caseId)

    ranked.value = threadData.ranked
    features.value = threadData.features

    const featureMap = groupFeaturesByType(features.value)

    if (serverRanking) {
      applyServerRanking(featureMap, serverRanking)
    }

    groupedFeatures.value = Array.from(featureMap.values())
    localStorageKey.value = `featureOrder_${caseId}`
    saveToLocalStorage(caseId)
  }

  const threadData = await fetchEmailThreads(caseId)
  if (threadData) {
    messages.value = threadData.messages
    features.value = threadData.features
    ranked.value = threadData.ranked
  }
}

onMounted(() => {
  const caseId = route.params.id
  if (caseId) {
    loadCaseData(caseId)
  }
})

watch(() => route.params.id, (newId) => {
  if (newId) loadCaseData(newId)
}, { immediate: true })

function navigateToPreviousCase() {
  if (!canGoPrev.value) return
  const prev = rankingThreadsList.value[currentIndex.value - 1]
  router.push({ name: 'RankerDetail', params: { id: prev.thread_id.toString() } })
}

function navigateToNextCase() {
  if (!canGoNext.value) return
  const next = rankingThreadsList.value[currentIndex.value + 1]
  router.push({ name: 'RankerDetail', params: { id: next.thread_id.toString() } })
}

function navigateBackToRanker() {
  router.push({ name: 'Ranker' })
}
</script>

<style scoped>
.content-panels {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* Panels */
.panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
}

.features-panel {
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.panel-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.panel-title {
  font-weight: 600;
  font-size: 0.95rem;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* Resize Divider */
.resize-divider {
  width: 6px;
  background: rgba(var(--v-theme-on-surface), 0.05);
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background-color 0.2s;
}

.resize-divider:hover,
.resize-divider.resizing {
  background: rgba(var(--v-theme-primary), 0.15);
}

.resize-handle {
  width: 3px;
  height: 40px;
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 2px;
}

.resize-divider:hover .resize-handle,
.resize-divider.resizing .resize-handle {
  background: rgb(var(--v-theme-primary));
}

/* Buckets */
.buckets-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.bucket {
  flex: 1;
  min-height: 200px;
  padding: 12px;
  border-radius: 8px;
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
  min-height: 100px;
}

.good-bucket {
  background-color: rgba(var(--v-theme-success), 0.08);
  border: 1px solid rgba(var(--v-theme-success), 0.3);
}

.average-bucket {
  background-color: rgba(var(--v-theme-warning), 0.08);
  border: 1px solid rgba(var(--v-theme-warning), 0.3);
}

.bad-bucket {
  background-color: rgba(var(--v-theme-error), 0.08);
  border: 1px solid rgba(var(--v-theme-error), 0.3);
}

.neutral-bucket {
  background-color: rgba(var(--v-theme-surface-variant), 0.5);
  border: 1px solid rgb(var(--v-theme-surface-variant));
  padding: 12px;
  border-radius: 8px;
  margin-top: 8px;
}

.neutral-bucket h4 {
  margin: 0 0 8px 0;
  font-size: 0.875rem;
  font-weight: 600;
}

.neutral-content {
  min-height: 60px;
}

.bucket-item {
  background-color: rgb(var(--v-theme-surface));
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 8px;
  cursor: grab;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  position: relative;
  font-size: 0.875rem;
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

/* Drag & Drop */
.sortable-ghost {
  opacity: 0.4;
}

.sortable-chosen {
  background-color: rgba(var(--v-theme-primary), 0.15);
}

/* Mobile Styles */
.content-panels.is-mobile {
  flex-direction: column;
  max-width: 100vw;
  overflow-x: hidden;
}

.content-panels.is-mobile .features-panel {
  flex: 1 !important;
  width: 100% !important;
  border-right: none;
  min-height: 0;
}

.content-panels.is-mobile .panel-header {
  padding: 10px 12px;
}

.content-panels.is-mobile .panel-content {
  padding: 12px;
}

.content-panels.is-mobile .buckets-row {
  flex-direction: column;
  gap: 8px;
}

.content-panels.is-mobile .bucket {
  flex: none;
  width: 100%;
}
</style>
