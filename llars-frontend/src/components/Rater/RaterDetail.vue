<template>
  <LEvaluationLayout
    :title="threadTitle"
    :subtitle="$t('rater.detail.threadLabel', { id: route.params.id })"
    :back-label="$t('rater.detail.backLabel')"
    :status="evaluationStatus"
    :can-go-prev="canGoPrev"
    :can-go-next="canGoNext"
    :current-index="currentIndex"
    :total-items="ratingThreadsList.length"
    @back="navigateBackToRater"
    @prev="navigateToPreviousCase"
    @next="navigateToNextCase"
  >
    <!-- Main Content -->
    <div ref="containerRef" class="content-panels" :class="{ 'is-mobile': isMobile }">
      <!-- Loading State -->
      <template v-if="isLoading('data')">
        <div class="panel left-panel">
          <v-skeleton-loader type="card" class="fill-height" />
        </div>
        <div class="panel right-panel">
          <v-skeleton-loader type="card" class="fill-height" />
        </div>
      </template>

      <!-- Loaded Content -->
      <template v-else>
        <!-- Feature-Bereich (links) -->
        <div class="panel features-panel" :style="leftPanelStyle()">
          <div class="panel-header">
            <LIcon size="20" class="mr-2">mdi-format-list-bulleted</LIcon>
            <span class="panel-title">{{ $t('rater.detail.featuresTitle') }}</span>
            <v-spacer />
            <LTooltip v-if="ratedCount > 0" :text="$t('rater.detail.progressTooltip')">
              <LTag variant="info" size="small">
                {{ ratedCount }} / {{ totalFeatures }}
              </LTag>
            </LTooltip>
          </div>
          <div class="panel-content">
            <v-expansion-panels>
              <v-expansion-panel v-for="featureGroup in groupedFeatures" :key="featureGroup.type">
                <v-expansion-panel-title>
                  <div>{{ translateFeatureType(featureGroup.type) }}</div>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <div v-for="feature in featureGroup.details" :key="feature.feature_id" class="feature-item">
                    <v-card class="feature-card" @click="navigateToFeatureDetail(feature.feature_id)">
                      <v-card-title class="feature-card-title d-flex align-center">
                        <span>{{ feature.model_name }}</span>
                        <v-spacer />
                        <LIcon
                          v-if="feature.user_rating !== null && feature.user_rating !== undefined"
                          color="success"
                          size="18"
                        >
                          mdi-check-circle
                        </LIcon>
                        <LIcon v-else color="grey" size="18">mdi-circle-outline</LIcon>
                      </v-card-title>
                      <v-card-text class="feature-card-text">{{ feature.content }}</v-card-text>
                    </v-card>
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
            <span class="panel-title">{{ $t('rater.detail.emailHistory') }}</span>
          </div>
          <div class="panel-content">
            <LMessageList :messages="messages" />
          </div>
        </div>
      </template>
    </div>
  </LEvaluationLayout>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { usePanelResize } from '@/composables/usePanelResize'
import { useMobile } from '@/composables/useMobile'

const { isMobile } = useMobile()
import { useActiveDuration, useScrollDepth } from '@/composables/useAnalyticsMetrics'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const features = ref([])
const messages = ref([])
const groupedFeatures = ref([])
const rated = ref(null)
const ratingThreadsList = ref([])
const threadTitle = ref(t('rater.detail.defaultTitle'))

// Skeleton Loading
const { isLoading, withLoading } = useSkeletonLoading(['data'])

// Panel Resize
const {
  isResizing,
  containerRef,
  startResize,
  leftPanelStyle,
  rightPanelStyle
} = usePanelResize({
  initialLeftPercent: 50,
  minLeftPercent: 25,
  maxLeftPercent: 75,
  storageKey: 'rater-panel-width'
})

// ==================== ANALYTICS ====================

// Entity dimension for this thread
const evalEntity = computed(() => `thread:${route.params.id}`)

// Session active time tracking
useActiveDuration({
  category: 'eval',
  action: 'session_active_ms',
  name: () => evalEntity.value,
  dimensions: () => ({ entity: evalEntity.value, view: 'overview' })
})

// Scroll depth for panels container
useScrollDepth(containerRef, {
  category: 'eval',
  action: 'scroll_depth',
  name: () => evalEntity.value,
  dimensions: () => ({ entity: evalEntity.value, view: 'overview' })
})

// Computed for progress tracking
const totalFeatures = computed(() => features.value.length)
const ratedCount = computed(() =>
  features.value.filter(f => f.user_rating !== null && f.user_rating !== undefined).length
)

// Navigation
const currentIndex = computed(() => {
  const id = Number(route.params.id)
  return ratingThreadsList.value.findIndex(t => t.thread_id === id)
})
const canGoPrev = computed(() => currentIndex.value > 0)
const canGoNext = computed(() => currentIndex.value >= 0 && currentIndex.value < ratingThreadsList.value.length - 1)

// Evaluation status for LEvaluationStatus component
const evaluationStatus = computed(() => {
  if (rated.value === null) return 'pending'
  if (rated.value) return 'done'
  if (ratedCount.value > 0) return 'in_progress'
  return 'pending'
})

async function fetchEmailThread(threadId) {
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/ratings/${threadId}`)
    return response.data
  } catch (error) {
    console.error('Error fetching email thread:', error)
    return null
  }
}

async function fetchRatingThreads() {
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/ratings`)
    return Array.isArray(response.data) ? response.data : []
  } catch (error) {
    console.error('Error fetching rating threads:', error)
    return []
  }
}

async function loadCaseData(caseId) {
  rated.value = null

  // Lade Thread-Liste für Navigation
  const threads = await fetchRatingThreads()
  if (threads) {
    ratingThreadsList.value = threads
    const currentThread = threads.find(t => t.thread_id === parseInt(caseId))
    if (currentThread) {
      threadTitle.value = currentThread.subject || t('rater.detail.defaultTitle')
    }
  }

  await withLoading('data', async () => {
    const threadData = await fetchEmailThread(caseId)
    if (!threadData) return

    features.value = Array.isArray(threadData.features) ? threadData.features : []
    messages.value = Array.isArray(threadData.messages) ? threadData.messages : []

    if (typeof threadData.rated === 'boolean') {
      rated.value = threadData.rated
    } else {
      rated.value = features.value.length > 0 && features.value.every(f => f.user_rating !== null && f.user_rating !== undefined)
    }

    const featureMap = new Map()
    features.value.forEach((f, index) => {
      if (!featureMap.has(f.type)) {
        featureMap.set(f.type, {
          type: f.type,
          details: []
        })
      }
      featureMap.get(f.type).details.push({
        model_name: f.model_name,
        content: f.content,
        feature_id: f.feature_id,
        user_rating: f.user_rating ?? null,
        position: index
      })
    })
    groupedFeatures.value = Array.from(featureMap.values())
  })
}

watch(
  () => route.params.id,
  (newId) => {
    if (!newId) return
    void loadCaseData(newId)
  },
  { immediate: true }
)

function translateFeatureType(type) {
  const translations = {
    abstract_summary: t('rater.featureTypes.abstractSummary'),
    generated_category: t('rater.featureTypes.generatedCategory'),
    generated_subject: t('rater.featureTypes.generatedSubject'),
    order_clarification: t('rater.featureTypes.orderClarification'),
  }
  return translations[type] || type
}

function navigateToPreviousCase() {
  if (!canGoPrev.value) return
  const prev = ratingThreadsList.value[currentIndex.value - 1]
  router.push({ name: 'RaterDetail', params: { id: String(prev.thread_id) } })
}

function navigateToNextCase() {
  if (!canGoNext.value) return
  const next = ratingThreadsList.value[currentIndex.value + 1]
  router.push({ name: 'RaterDetail', params: { id: String(next.thread_id) } })
}

function navigateBackToRater() {
  router.push({ name: 'Rater' })
}

function navigateToFeatureDetail(featureId) {
  const threadId = route.params.id
  router.push({ name: 'RaterDetailFeature', params: { id: String(threadId), feature: String(featureId) } })
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

/* Feature Cards */
.feature-item {
  margin-bottom: 12px;
}

.feature-card {
  cursor: pointer;
  transition: box-shadow 0.2s ease;
}

.feature-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.12);
}

.feature-card-title {
  font-size: 0.95rem;
  font-weight: 600;
  padding-bottom: 4px;
}

.feature-card-text {
  font-size: 0.875rem;
  opacity: 0.85;
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

.content-panels.is-mobile .feature-item {
  margin-bottom: 8px;
}

.content-panels.is-mobile .feature-card {
  padding: 10px;
}
</style>
