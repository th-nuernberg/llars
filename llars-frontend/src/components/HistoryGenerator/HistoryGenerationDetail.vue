<template>
  <LEvaluationLayout
    ref="layoutRef"
    :title="headerTitle"
    :subtitle="$t('historyGeneration.detail.threadLabel', { id: threadId })"
    :back-label="$t('historyGeneration.detail.backLabel')"
    :error="loadError"
    :status="evaluationStatus"
    :saving="saving"
    :can-go-prev="canGoPrev"
    :can-go-next="canGoNext"
    :current-index="currentIndex"
    :total-items="caseList.length"
    @back="goOverview"
    @prev="goPrev"
    @next="goNext"
    @clear-error="loadError = ''"
  >
    <!-- Main Content -->
    <div ref="containerRef" class="content-panels">
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
        <!-- Left Panel: Messages -->
        <div class="panel left-panel" :style="leftPanelStyle()">
          <div class="panel-header">
            <LIcon size="20" class="mr-2">mdi-email-outline</LIcon>
            <span class="panel-title">{{ $t('historyGeneration.detail.messagePanelTitle') }}</span>
            <v-spacer />
            <LTag v-if="meta?.sender" variant="gray" size="small">{{ meta.sender }}</LTag>
          </div>
          <div class="panel-content">
            <div v-if="messages.length === 0" class="empty-state">
              <LIcon size="48" color="grey-lighten-1">mdi-email-off-outline</LIcon>
              <p class="text-medium-emphasis mt-2">{{ $t('historyGeneration.detail.emptyMessages') }}</p>
            </div>

            <div v-else class="messages">
              <LMessage
                v-for="m in messages"
                :key="m.message_id"
                :sender="m.sender"
                :timestamp="m.timestamp"
              >
                <template #actions>
                  <LIconBtn
                    :icon="m.rating === 'up' ? 'mdi-thumb-up' : 'mdi-thumb-up-outline'"
                    :variant="m.rating === 'up' ? 'success' : 'default'"
                    size="small"
                    :tooltip="$t('historyGeneration.detail.helpful')"
                    @click="toggleMessageRating(m, 'up')"
                  />
                  <LIconBtn
                    :icon="m.rating === 'down' ? 'mdi-thumb-down' : 'mdi-thumb-down-outline'"
                    :variant="m.rating === 'down' ? 'danger' : 'default'"
                    size="small"
                    :tooltip="$t('historyGeneration.detail.notHelpful')"
                    @click="toggleMessageRating(m, 'down')"
                  />
                </template>
                <div v-html="formatContent(m.content)" />
              </LMessage>
            </div>
          </div>
        </div>

        <!-- Resize Divider -->
        <div
          class="resize-divider"
          :class="{ resizing: isResizing }"
          @mousedown="startResize"
        >
          <div class="resize-handle"></div>
        </div>

        <!-- Right Panel: Rating Form -->
        <div class="panel right-panel" :style="rightPanelStyle()">
          <div class="panel-header">
            <LIcon size="20" class="mr-2">llars:evaluation</LIcon>
            <span class="panel-title">{{ $t('historyGeneration.detail.ratingTitle') }}</span>
          </div>
          <div class="panel-content">
            <v-alert v-if="saveError" type="error" variant="tonal" density="compact" class="mb-4" closable @click:close="saveError = ''">
              {{ saveError }}
            </v-alert>

            <!-- Rating Section 1: Kohärenz -->
            <div class="rating-section">
              <div class="section-header">
                <span class="section-number">1</span>
                <div class="section-info">
                  <h4>{{ $t('historyGeneration.detail.sections.coherence.title') }}</h4>
                  <p class="text-caption text-medium-emphasis">
                    {{ $t('historyGeneration.detail.sections.coherence.description') }}
                  </p>
                </div>
              </div>

              <div class="subsection" :class="{ disabled: disabledStates.client }">
                <span class="subsection-label">{{ $t('historyGeneration.detail.sections.coherence.clientLabel') }}</span>
                <LikertScale v-model="ratings.client_coherence" :disabled="disabledStates.client" />
              </div>

              <div class="subsection" :class="{ disabled: disabledStates.counsellor }">
                <span class="subsection-label">{{ $t('historyGeneration.detail.sections.coherence.counsellorLabel') }}</span>
                <LikertScale v-model="ratings.counsellor_coherence" :disabled="disabledStates.counsellor" />
              </div>
            </div>

            <!-- Rating Section 2: Qualität -->
            <div class="rating-section" :class="{ disabled: disabledStates.quality }">
              <div class="section-header">
                <span class="section-number">2</span>
                <div class="section-info">
                  <h4>{{ $t('historyGeneration.detail.sections.quality.title') }}</h4>
                  <p class="text-caption text-medium-emphasis">
                    {{ $t('historyGeneration.detail.sections.quality.description') }}
                  </p>
                </div>
              </div>
              <LikertScale v-model="ratings.quality" :disabled="disabledStates.quality" />
            </div>

            <!-- Rating Section 3: Gesamt -->
            <div class="rating-section" :class="{ disabled: disabledStates.overall }">
              <div class="section-header">
                <span class="section-number">3</span>
                <div class="section-info">
                  <h4>{{ $t('historyGeneration.detail.sections.overall.title') }}</h4>
                  <p class="text-caption text-medium-emphasis">
                    {{ $t('historyGeneration.detail.sections.overall.description') }}
                  </p>
                </div>
              </div>
              <BinaryLikertScale v-model="ratings.overall" :disabled="disabledStates.overall" />
            </div>

            <!-- Category Selection -->
            <div class="rating-section">
              <div class="section-header">
                <LIcon size="18" class="section-icon">mdi-tag-outline</LIcon>
                <div class="section-info">
                  <h4>{{ $t('historyGeneration.detail.sections.category.title') }}</h4>
                </div>
              </div>
              <v-select
                v-model="selectedCategoryId"
                :items="categories"
                item-title="name"
                item-value="id"
                :label="$t('historyGeneration.detail.sections.category.selectLabel')"
                variant="outlined"
                density="compact"
                clearable
                hide-details
                :disabled="categories.length === 0"
              />
              <v-textarea
                v-model="categoryNotes"
                :label="$t('historyGeneration.detail.sections.category.notesLabel')"
                variant="outlined"
                density="compact"
                auto-grow
                rows="2"
                hide-details
                class="mt-2"
              />
            </div>

            <!-- Notes -->
            <div class="rating-section">
              <div class="section-header">
                <LIcon size="18" class="section-icon">mdi-note-text-outline</LIcon>
                <div class="section-info">
                  <h4>{{ $t('historyGeneration.detail.sections.notes.title') }}</h4>
                </div>
              </div>
              <v-textarea
                v-model="feedback"
                :label="$t('historyGeneration.detail.sections.notes.label')"
                variant="outlined"
                auto-grow
                rows="3"
                hide-details
              />
            </div>
          </div>
        </div>
      </template>
    </div>
  </LEvaluationLayout>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import DOMPurify from 'dompurify'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { usePanelResize } from '@/composables/usePanelResize'
import LikertScale from '@/components/parts/LikertScale.vue'
import BinaryLikertScale from '@/components/parts/BinaryLikertScale.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const threadId = computed(() => Number(route.params.id))

// Refs
const layoutRef = ref(null)

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
  initialLeftPercent: 55,
  minLeftPercent: 30,
  maxLeftPercent: 70,
  storageKey: 'history-generation-panel-width'
})

// Data
const meta = ref(null)
const caseList = ref([])
const categories = ref([])
const messages = ref([])

// Rating state
const ratings = reactive({
  counsellor_coherence: null,
  client_coherence: null,
  quality: null,
  overall: null
})
const feedback = ref('')
const selectedCategoryId = ref(null)
const categoryNotes = ref('')
const ratedStatus = ref(null)

// UI state
const loadError = ref('')
const saving = ref(false)
const saveError = ref('')
const isInitialized = ref(false)

const headerTitle = computed(() => meta.value?.subject || t('historyGeneration.detail.headerDefault'))

// Evaluation status for the layout
const evaluationStatus = computed(() => {
  // Check if any rating has been given
  const hasRatings = ratings.client_coherence !== null ||
                     ratings.counsellor_coherence !== null ||
                     ratings.quality !== null ||
                     ratings.overall !== null

  // Check if all required ratings are complete
  const allComplete = ratings.client_coherence !== null &&
                      ratings.counsellor_coherence !== null &&
                      (disabledStates.value.quality || ratings.quality !== null) &&
                      (disabledStates.value.overall || ratings.overall !== null)

  if (allComplete) return 'done'
  if (hasRatings) return 'in_progress'
  return 'pending'
})

const disabledStates = computed(() => {
  const client = typeof ratings.client_coherence === 'number' && ratings.client_coherence > 2
  const counsellor = typeof ratings.counsellor_coherence === 'number' && ratings.counsellor_coherence > 2
  const quality = client || counsellor
  const overall = quality || (typeof ratings.quality === 'number' && ratings.quality > 2)
  return { client, counsellor, quality, overall }
})

// Debounce helper
function debounce(fn, delay) {
  let timeout = null
  return (...args) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => fn(...args), delay)
  }
}

function normalizeScaleValue(value) {
  if (value === 0) return null
  if (typeof value === 'number') return value
  return null
}

function cleanedText(value) {
  const text = typeof value === 'string' ? value.trim() : ''
  return text.length > 0 ? text : null
}

function toDbValue(value, isDisabled) {
  if (isDisabled && (value === null || value === undefined)) return 0
  return value
}

function formatContent(content) {
  if (!content) return ''
  const sanitizedContent = String(content).replace(/\n/g, '<br>')
  return DOMPurify.sanitize(sanitizedContent, {
    ALLOWED_TAGS: ['br', 'a'],
    ALLOWED_ATTR: ['href']
  })
}

function toggleMessageRating(message, value) {
  const next = message.rating === value ? null : value
  messages.value = messages.value.map(m => (m.message_id === message.message_id ? { ...m, rating: next } : m))
}

// Auto-save function
const autoSave = debounce(async () => {
  if (!isInitialized.value) return

  const id = threadId.value
  if (!Number.isFinite(id) || id <= 0) return

  saving.value = true
  saveError.value = ''

  try {
    const base = import.meta.env.VITE_API_BASE_URL

    const anyDisabled =
      disabledStates.value.client ||
      disabledStates.value.counsellor ||
      disabledStates.value.quality ||
      disabledStates.value.overall

    const mailPayload = {
      counsellor_coherence_rating: toDbValue(ratings.counsellor_coherence, disabledStates.value.counsellor),
      client_coherence_rating: toDbValue(ratings.client_coherence, disabledStates.value.client),
      quality_rating: toDbValue(ratings.quality, disabledStates.value.quality),
      overall_rating: toDbValue(ratings.overall, disabledStates.value.overall),
      feedback: cleanedText(feedback.value),
      consulting_category_id: selectedCategoryId.value ?? null,
      consulting_category_notes: cleanedText(categoryNotes.value),
      consider_category_for_status: !anyDisabled
    }

    const messagePayload = {
      message_ratings: messages.value.map(m => ({
        message_id: m.message_id,
        rating: m.rating ?? null
      }))
    }

    await axios.post(`${base}/api/email_threads/save_mailhistory_rating/${id}`, mailPayload)
    await axios.post(`${base}/api/email_threads/save_message_ratings/${id}`, messagePayload)

    // Refresh status
    try {
      const res = await axios.get(`${base}/api/email_threads/mailhistory_ratings/${id}`)
      ratedStatus.value = res.data?.rating?.rating_status || ratedStatus.value
    } catch {
      // ignore
    }

  } catch (e) {
    saveError.value =
      e?.response?.data?.error ||
      e?.response?.data?.message ||
      e?.message ||
      t('historyGeneration.detail.errors.saveFailed')
  } finally {
    saving.value = false
  }
}, 800)

async function loadData() {
  const id = threadId.value
    if (!Number.isFinite(id) || id <= 0) {
    loadError.value = t('historyGeneration.detail.errors.invalidThread')
    return
  }

  loadError.value = ''
  saveError.value = ''
  isInitialized.value = false

  await withLoading('data', async () => {
    try {
      const base = import.meta.env.VITE_API_BASE_URL

      const [threadsRes, messagesRes, msgRatingsRes, mailRatingRes, categoriesRes] = await Promise.all([
        axios.get(`${base}/api/email_threads/mailhistory_ratings`),
        axios.get(`${base}/api/email_threads/generations/${id}`),
        axios.get(`${base}/api/email_threads/message_ratings/${id}`),
        axios.get(`${base}/api/email_threads/mailhistory_ratings/${id}`),
        axios.get(`${base}/api/email_threads/consulting_category_types`)
      ])

      caseList.value = threadsRes.data?.threads || []
      meta.value = caseList.value.find(t => t.thread_id === id) || null

      const cats = categoriesRes.data?.consulting_category_types || categoriesRes.data?.data || []
      categories.value = Array.isArray(cats) ? cats : []

      const rawMessages = messagesRes.data?.messages || []
      const rawMsgRatings = Array.isArray(msgRatingsRes.data) ? msgRatingsRes.data : []
      const ratingByMessageId = new Map(rawMsgRatings.map(r => [r.message_id, r.rating]))

      messages.value = rawMessages.map(m => ({
        ...m,
        rating: ratingByMessageId.has(m.message_id) ? ratingByMessageId.get(m.message_id) : null
      }))

      const ratingData = mailRatingRes.data?.rating || {}
      ratings.counsellor_coherence = normalizeScaleValue(ratingData.counsellor_coherence_rating)
      ratings.client_coherence = normalizeScaleValue(ratingData.client_coherence_rating)
      ratings.quality = normalizeScaleValue(ratingData.quality_rating)
      ratings.overall = normalizeScaleValue(ratingData.overall_rating)

      feedback.value = ratingData.feedback ?? ''
      ratedStatus.value = ratingData.rating_status || null

      const consultingCategory = mailRatingRes.data?.consulting_category || {}
      selectedCategoryId.value = consultingCategory.consulting_category_type_id ?? null
      categoryNotes.value = consultingCategory.consulting_category_note ?? ''

      // Mark as initialized after a short delay
      setTimeout(() => {
        isInitialized.value = true
      }, 100)

    } catch (e) {
      loadError.value =
        e?.response?.data?.error ||
        e?.response?.data?.message ||
        e?.message ||
        t('historyGeneration.detail.errors.loadFailed')
    }
  })
}

function goOverview() {
  router.push({ name: 'HistoryGenerator' })
}

const currentIndex = computed(() => caseList.value.findIndex(t => t.thread_id === threadId.value))
const canGoPrev = computed(() => currentIndex.value > 0)
const canGoNext = computed(() => currentIndex.value >= 0 && currentIndex.value < caseList.value.length - 1)

function goPrev() {
  if (!canGoPrev.value) return
  const prev = caseList.value[currentIndex.value - 1]
  router.push({ name: 'HistoryGenerationDetail', params: { id: String(prev.thread_id) } })
}

function goNext() {
  if (!canGoNext.value) return
  const next = caseList.value[currentIndex.value + 1]
  router.push({ name: 'HistoryGenerationDetail', params: { id: String(next.thread_id) } })
}

// Watch for changes and auto-save
watch(
  [ratings, feedback, selectedCategoryId, categoryNotes],
  () => {
    if (isInitialized.value) {
      autoSave()
    }
  },
  { deep: true }
)

// Watch message ratings separately
watch(
  () => messages.value.map(m => m.rating),
  () => {
    if (isInitialized.value) {
      autoSave()
    }
  },
  { deep: true }
)

watch(
  () => threadId.value,
  async () => {
    await loadData()
  },
  { immediate: true }
)
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

.left-panel {
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

/* Messages */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 16px;
  text-align: center;
}

.messages {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Rating Sections */
.rating-section {
  padding: 16px;
  background: rgba(var(--v-theme-surface-variant), 0.2);
  border-radius: 12px;
  margin-bottom: 16px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.rating-section.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.section-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.section-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: rgb(var(--v-theme-primary));
  color: white;
  border-radius: 50%;
  font-size: 0.8rem;
  font-weight: 600;
  flex-shrink: 0;
}

.section-icon {
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-top: 2px;
}

.section-info h4 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
}

.section-info p {
  margin: 2px 0 0 0;
}

.subsection {
  padding: 12px;
  background: rgba(var(--v-theme-surface), 0.5);
  border-radius: 8px;
  margin-top: 10px;
}

.subsection.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.subsection-label {
  display: block;
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin-bottom: 8px;
}
</style>
