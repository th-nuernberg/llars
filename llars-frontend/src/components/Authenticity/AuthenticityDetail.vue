<template>
  <LEvaluationLayout
    ref="layoutRef"
    :title="thread?.subject || $t('authenticity.detail.defaultTitle')"
    :subtitle="$t('authenticity.detail.threadLabel', { id: threadId })"
    :back-label="$t('authenticity.detail.backLabel')"
    :error="loadError"
    :status="evaluationStatus"
    :saving="saving || savingMetadata"
    :can-go-prev="canGoPrev"
    :can-go-next="canGoNext"
    :current-index="currentIndex"
    :total-items="threadList.length"
    @back="goBack"
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
            <span class="panel-title">{{ $t('authenticity.detail.messagePanelTitle') }}</span>
            <v-spacer />
            <LTag v-if="thread?.sender" variant="gray" size="small">{{ thread.sender }}</LTag>
          </div>
          <div class="panel-content">
            <LMessageList :messages="thread?.messages || []" />
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

        <!-- Right Panel: Voting -->
        <div class="panel right-panel" :style="rightPanelStyle()">
          <div class="panel-header">
            <LIcon size="20" class="mr-2">mdi-check-decagram</LIcon>
            <span class="panel-title">{{ $t('authenticity.detail.votePanelTitle') }}</span>
          </div>
          <div class="panel-content">
            <!-- Info Box -->
            <div class="info-box">
              <LIcon size="18" class="mr-2">mdi-information-outline</LIcon>
              <i18n-t keypath="authenticity.detail.infoText" tag="span">
                <strong>{{ $t('authenticity.detail.fakeLabel') }}</strong>
              </i18n-t>
            </div>

            <!-- Vote Buttons -->
            <div class="vote-section">
              <h4 class="section-title">{{ $t('authenticity.detail.voteQuestion') }}</h4>
              <div class="vote-buttons">
                <button
                  class="vote-btn vote-real"
                  :class="{ selected: voteState.vote === 'real' }"
                  @click="submitVote('real')"
                  :disabled="saving"
                >
                  <LIcon size="24">mdi-account-check</LIcon>
                  <span>{{ $t('authenticity.detail.voteReal') }}</span>
                  <span class="vote-hint">{{ $t('authenticity.detail.voteRealHint') }}</span>
                </button>
                <button
                  class="vote-btn vote-fake"
                  :class="{ selected: voteState.vote === 'fake' }"
                  @click="submitVote('fake')"
                  :disabled="saving"
                >
                  <LIcon size="24">mdi-robot</LIcon>
                  <span>{{ $t('authenticity.detail.voteFake') }}</span>
                  <span class="vote-hint">{{ $t('authenticity.detail.voteFakeHint') }}</span>
                </button>
              </div>
            </div>

            <!-- Confidence Slider -->
            <div class="metadata-section">
              <div class="d-flex align-center mb-2">
                <span class="section-label">{{ $t('authenticity.detail.confidenceLabel') }}</span>
                <v-fade-transition>
                  <LIcon
                    v-if="savingMetadata"
                    size="14"
                    class="ml-2 saving-indicator"
                    color="primary"
                  >
                    mdi-cloud-sync
                  </LIcon>
                </v-fade-transition>
              </div>
              <LSlider
                v-model="voteState.confidence"
                :min="0"
                :max="100"
                :step="5"
                :start-active="hasExistingConfidence"
                density="compact"
                @touched="onConfidenceTouched"
              />
            </div>

            <!-- Notes -->
            <div class="metadata-section">
              <span class="section-label">{{ $t('authenticity.detail.notesLabel') }}</span>
              <v-textarea
                v-model="voteState.notes"
                variant="outlined"
                density="compact"
                auto-grow
                rows="2"
                hide-details
                :placeholder="$t('authenticity.detail.notesPlaceholder')"
              />
            </div>

            <v-alert v-if="error" type="error" variant="tonal" class="mt-4" density="compact">
              {{ error }}
            </v-alert>
          </div>
        </div>
      </template>
    </div>
  </LEvaluationLayout>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { usePanelResize } from '@/composables/usePanelResize'
import {
  getAuthenticityThread,
  listAuthenticityThreads,
  saveAuthenticityVote,
  updateAuthenticityMetadata
} from '@/services/authenticityApi'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const threadId = computed(() => Number(route.params.id))

// Refs
const layoutRef = ref(null)

// Skeleton Loading
const { isLoading, setLoading, withLoading } = useSkeletonLoading(['data'])

// Panel Resize
const {
  isResizing,
  containerRef,
  startResize,
  leftPanelStyle,
  rightPanelStyle
} = usePanelResize({
  initialLeftPercent: 60,
  minLeftPercent: 40,
  maxLeftPercent: 75,
  storageKey: 'authenticity-panel-width'
})

// Data
const thread = ref(null)
const threadList = ref([])
const saving = ref(false)
const savingMetadata = ref(false)
const loadError = ref('')
const error = ref('')
const initialLoadDone = ref(false)

const voteState = ref({
  vote: null,
  confidence: 50,
  notes: ''
})

const hasExistingConfidence = ref(false)
const confidenceTouched = ref(false)

// Handler for slider touched event
function onConfidenceTouched() {
  confidenceTouched.value = true
}

// Computed
const evaluationStatus = computed(() => {
  if (voteState.value.vote) return 'done'
  if (hasExistingConfidence.value || voteState.value.notes) return 'in_progress'
  return 'pending'
})

const currentIndex = computed(() => threadList.value.findIndex(t => t.thread_id === threadId.value))
const canGoPrev = computed(() => currentIndex.value > 0)
const canGoNext = computed(() => currentIndex.value >= 0 && currentIndex.value < threadList.value.length - 1)

// Debounce helper
function debounce(fn, delay) {
  let timeout = null
  return (...args) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => fn(...args), delay)
  }
}

// Save metadata with debounce
const saveMetadata = debounce(async (data) => {
  if (!initialLoadDone.value) return
  savingMetadata.value = true
  try {
    await updateAuthenticityMetadata(threadId.value, data)
  } catch (e) {
    console.error('Failed to save metadata:', e)
  } finally {
    savingMetadata.value = false
  }
}, 500)

// Watch confidence changes - only save if slider was touched
watch(() => voteState.value.confidence, (newVal, oldVal) => {
  if (initialLoadDone.value && newVal !== oldVal && (confidenceTouched.value || hasExistingConfidence.value)) {
    saveMetadata({ confidence: newVal })
  }
})

// Watch notes changes
watch(() => voteState.value.notes, (newVal, oldVal) => {
  if (initialLoadDone.value && newVal !== oldVal) {
    saveMetadata({ notes: newVal })
  }
})

// Navigation
function goBack() {
  router.push({ name: 'AuthenticityOverview' })
}

function goPrev() {
  if (!canGoPrev.value) return
  const prev = threadList.value[currentIndex.value - 1]
  router.push({ name: 'AuthenticityDetail', params: { id: String(prev.thread_id) } })
}

function goNext() {
  if (!canGoNext.value) return
  const next = threadList.value[currentIndex.value + 1]
  router.push({ name: 'AuthenticityDetail', params: { id: String(next.thread_id) } })
}

// Load data
async function load() {
  loadError.value = ''
  error.value = ''
  initialLoadDone.value = false
  hasExistingConfidence.value = false
  confidenceTouched.value = false

  // Clear old thread data immediately to prevent mixing
  thread.value = null
  voteState.value = { vote: null, confidence: 50, notes: '' }

  try {
    await withLoading('data', async () => {
      // Load thread list for navigation
      const list = await listAuthenticityThreads()
      threadList.value = Array.isArray(list) ? list : []

      // Load current thread
      const data = await getAuthenticityThread(threadId.value)
      thread.value = data

      if (data?.vote) {
        voteState.value.vote = data.vote.vote || null
        voteState.value.confidence = typeof data.vote.confidence === 'number' ? data.vote.confidence : 50
        voteState.value.notes = data.vote.notes || ''
        hasExistingConfidence.value = typeof data.vote.confidence === 'number'
      } else {
        voteState.value.vote = null
        voteState.value.confidence = 50
        voteState.value.notes = ''
      }
    })
  } catch (e) {
    loadError.value = e?.response?.data?.message || e?.message || t('authenticity.detail.errors.loadFailed')
  } finally {
    setLoading('data', false)
    setTimeout(() => {
      initialLoadDone.value = true
    }, 100)
  }
}

// Submit vote (auto-save)
async function submitVote(vote) {
  error.value = ''
  saving.value = true

  try {
    // Only include confidence if the slider was touched or had existing value
    const payload = {
      vote,
      notes: voteState.value.notes
    }
    if (confidenceTouched.value || hasExistingConfidence.value) {
      payload.confidence = voteState.value.confidence
    }
    await saveAuthenticityVote(threadId.value, payload)
    voteState.value.vote = vote
  } catch (e) {
    error.value = e?.response?.data?.message || e?.message || t('authenticity.detail.errors.saveFailed')
  } finally {
    saving.value = false
  }
}

// Watch route changes
watch(() => threadId.value, async () => {
  await load()
}, { immediate: true })
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

/* Info Box */
.info-box {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  background: rgba(var(--v-theme-info), 0.1);
  border: 1px solid rgba(var(--v-theme-info), 0.2);
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

/* Vote Section */
.vote-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 12px;
}

.vote-buttons {
  display: flex;
  gap: 12px;
}

.vote-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px 16px;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.2);
  cursor: pointer;
  transition: all 0.2s ease;
}

.vote-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.vote-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.vote-btn span:first-of-type {
  font-size: 1.1rem;
  font-weight: 600;
}

.vote-hint {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.vote-real {
  border-color: rgba(76, 175, 80, 0.3);
}

.vote-real:hover:not(:disabled) {
  background: rgba(76, 175, 80, 0.1);
  border-color: rgba(76, 175, 80, 0.5);
}

.vote-real.selected {
  background: rgba(76, 175, 80, 0.15);
  border-color: #4CAF50;
  box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.2);
}

.vote-fake {
  border-color: rgba(232, 160, 135, 0.3);
}

.vote-fake:hover:not(:disabled) {
  background: rgba(232, 160, 135, 0.1);
  border-color: rgba(232, 160, 135, 0.5);
}

.vote-fake.selected {
  background: rgba(232, 160, 135, 0.15);
  border-color: #e8a087;
  box-shadow: 0 0 0 3px rgba(232, 160, 135, 0.2);
}

/* Metadata Sections */
.metadata-section {
  margin-bottom: 16px;
}

.section-label {
  display: block;
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 8px;
}

.saving-indicator {
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}
</style>
