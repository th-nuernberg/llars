<template>
  <div class="authenticity-interface" ref="containerRef">
    <!-- Left Panel: Content to Evaluate -->
    <div class="left-panel" :style="leftPanelStyle()">
      <!-- Panel Header. Shown with the title when standalone; when embedded
           in EvaluationSession the title row is hidden but we still render a
           slim header on mobile so the fullscreen-read trigger has a home. -->
      <div v-if="!hideNavigation || isMobile" class="panel-header content-panel-header">
        <template v-if="!hideNavigation">
          <LIcon size="20" class="mr-2">mdi-email-outline</LIcon>
          <h3>{{ $t('authenticity.detail.messagePanelTitle') }}</h3>
        </template>
        <v-spacer />
        <!-- Mobile-only fullscreen read button: the left panel is capped at
             ~40vh on phones, so long histories are unreadable. This opens the
             same content in a fullscreen overlay. Hidden on desktop. -->
        <LIconBtn
          v-if="isMobile"
          icon="mdi-fullscreen"
          variant="text"
          size="small"
          :tooltip="$t('authenticity.detail.readFullscreen')"
          @click="openFullscreen"
        />
      </div>

      <!-- Content Panel -->
      <div class="panel-content">
        <div v-if="loadingItem" class="loading-state">
          <v-progress-circular indeterminate color="primary" size="32" />
        </div>
        <LMessageList v-else-if="messages.length > 0" :messages="messages" />
        <div v-else-if="content" class="content-text">{{ content }}</div>
        <div v-else class="empty-state">
          <LIcon size="48" color="grey-lighten-1">mdi-text-box-off-outline</LIcon>
          <p>{{ $t('authenticity.detail.noContent') }}</p>
        </div>
      </div>
    </div>

    <!-- Resize Handle -->
    <div class="resize-handle" @mousedown="startResize">
      <div class="handle-line" />
    </div>

    <!-- Right Panel: Voting -->
    <div class="right-panel" :style="rightPanelStyle()">
      <!-- Panel Header (hidden when embedded in EvaluationSession) -->
      <div v-if="!hideNavigation" class="panel-header">
        <LIcon size="20" class="mr-2">mdi-shield-search</LIcon>
        <h3>{{ $t('authenticity.detail.votePanelTitle') }}</h3>
        <v-spacer />
        <!-- Status Chip -->
        <LEvaluationStatus
          :status="currentItemStatus"
          :saving="saving"
        />
      </div>

      <div v-if="currentItem" class="panel-content">
        <!-- Info Box -->
        <div class="info-box">
          <LIcon size="18" class="mr-2">mdi-information-outline</LIcon>
          <span>{{ $t('authenticity.detail.infoText') }}</span>
        </div>

        <!-- Vote Buttons -->
        <div class="vote-section">
          <h4 class="section-title">{{ $t('authenticity.detail.voteQuestion') }}</h4>
          <div class="vote-buttons">
            <button
              class="vote-btn vote-real"
              :class="{ selected: vote === 'real' }"
              @click="submitVote('real')"
              :disabled="saving"
            >
              <LIcon size="28">mdi-account-check</LIcon>
              <span class="vote-label">{{ realLabel }}</span>
              <span class="vote-hint">{{ $t('authenticity.detail.voteRealHint') }}</span>
            </button>
            <button
              class="vote-btn vote-fake"
              :class="{ selected: vote === 'fake' }"
              @click="submitVote('fake')"
              :disabled="saving"
            >
              <LIcon size="28">mdi-robot</LIcon>
              <span class="vote-label">{{ fakeLabel }}</span>
              <span class="vote-hint">{{ $t('authenticity.detail.voteFakeHint') }}</span>
            </button>
          </div>
        </div>

        <!-- Confidence + notes: collapsed by default behind a chevron toggle
             so the secondary metadata stops crowding the vote buttons on
             mobile. Auto-expands when an existing note is loaded (see
             metaExpanded watcher). -->
        <div class="metadata-group" :class="{ expanded: metaExpanded }">
          <button class="metadata-toggle" type="button" @click="metaExpanded = !metaExpanded">
            <LIcon size="14" class="mr-1">
              {{ metaExpanded ? 'mdi-chevron-down' : 'mdi-chevron-right' }}
            </LIcon>
            <span>{{ $t('authenticity.detail.detailsLabel') }}</span>
            <span v-if="notes && !metaExpanded" class="metadata-hint">({{ notes.length }})</span>
          </button>

          <template v-if="metaExpanded">
            <!-- Confidence Slider -->
            <div class="metadata-section">
              <span class="section-label">{{ $t('authenticity.detail.confidenceLabel') }}</span>
              <LSlider
                v-model="confidence"
                :min="0"
                :max="100"
                :step="5"
                density="compact"
                @update:model-value="onConfidenceChange"
              />
            </div>

            <!-- Notes -->
            <div class="metadata-section">
              <span class="section-label">{{ $t('authenticity.detail.notesLabel') }}</span>
              <v-textarea
                v-model="notes"
                variant="outlined"
                density="compact"
                auto-grow
                rows="2"
                hide-details
                :placeholder="$t('authenticity.detail.notesPlaceholder')"
                @blur="saveMetadata"
              />
            </div>
          </template>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="empty-state">
        <LIcon size="48" color="grey-lighten-1">mdi-shield-off-outline</LIcon>
        <h3>{{ $t('authenticity.detail.emptyTitle') }}</h3>
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

    <!-- Mobile-only fullscreen read overlay for the message content. The left
         panel is capped at ~40vh on phones (≈150px), so long histories are
         unreadable inline. This renders the SAME content (LMessageList / text)
         fullscreen with a top bar + close button. Read-only — no vote button
         needed here (votes live in the right panel). Mirrors the proven
         ComparisonInterface pattern. -->
    <v-dialog
      v-model="fullscreenOpen"
      fullscreen
      :scrim="false"
      transition="dialog-bottom-transition"
    >
      <div class="content-fullscreen">
        <div class="content-fullscreen-bar">
          <LIcon size="20" class="mr-2">mdi-email-outline</LIcon>
          <span class="content-fullscreen-title">{{ $t('authenticity.detail.messagePanelTitle') }}</span>
          <v-spacer />
          <LBtn variant="text" size="small" prepend-icon="mdi-close" @click="fullscreenOpen = false">
            {{ $t('common.close') }}
          </LBtn>
        </div>
        <div class="content-fullscreen-content">
          <LMessageList v-if="messages.length > 0" :messages="messages" />
          <div v-else-if="content" class="content-text">{{ content }}</div>
          <div v-else class="empty-state">
            <LIcon size="48" color="grey-lighten-1">mdi-text-box-off-outline</LIcon>
            <p>{{ $t('authenticity.detail.noContent') }}</p>
          </div>
        </div>
      </div>
    </v-dialog>
  </div>
</template>

<script setup>
/**
 * AuthenticityInterface.vue - Fake/Real Voting Interface
 *
 * Provides the UI for authenticity evaluation where users vote
 * whether content is real (human-written) or fake (AI-generated).
 */
import { ref, computed, watch, onMounted, toRef } from 'vue'
import { useI18n } from 'vue-i18n'
import { usePanelResize } from '@/composables/usePanelResize'
import { useAuthenticityEvaluation } from '@/composables/useAuthenticityEvaluation'
import { useMobile } from '@/composables/useMobile'

const { t, locale } = useI18n()

// Localize a value that may be a plain string or a localized object {de, en}.
// api_v1-created scenarios store option labels as localized objects (canonical
// evaluation_data_schemas shape).
function localize(v) {
  if (v == null) return ''
  if (typeof v === 'string') return v
  return v[locale.value] || v.de || v.en || ''
}

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

// <600px — gates the mobile-only fullscreen-read button + the collapsed
// metadata defaults. Desktop keeps the full inline layout untouched.
const { isMobile } = useMobile()

// Panel resize composable
const { containerRef, leftPanelStyle, rightPanelStyle, startResize } = usePanelResize({
  initialLeftPercent: 55,
  minLeftPercent: 40,
  maxLeftPercent: 70,
  storageKey: 'llars-authenticity-panel-width'
})

// Authenticity evaluation composable
const scenarioIdRef = toRef(props, 'scenarioId')
const {
  items,
  currentItem,
  currentItemIndex,
  messages,
  content,
  vote,
  confidence,
  notes,
  loading,
  loadingItem,
  saving,
  error,
  progress,
  hasNext,
  hasPrev,
  currentItemStatus,
  loadItems,
  loadItem,
  submitVote: doSubmitVote,
  saveMetadata: doSaveMetadata,
  goNext,
  goPrev
} = useAuthenticityEvaluation(scenarioIdRef)

// Unwrap the (possibly nested) config_json. api_v1 scenarios store the
// canonical shape `{type, config: {options}}`; wizard scenarios nest under
// eval_config; manual scenarios pass the inner config directly.
const inner = computed(() =>
  props.config?.config || props.config?.eval_config?.config || props.config || {}
)

// The authenticity vote is binary (backend contract: 'real' | 'fake'). The
// canonical config exposes presentational `options` ([{id, label}]) where
// `human` maps to the "real" vote and `ai`/`llm` to the "fake" vote. We use
// those localized labels for the two buttons when present, falling back to the
// existing i18n strings — the submitted vote value is unchanged.
const authOptions = computed(() => inner.value?.options || [])

function findOptionLabel(...ids) {
  const opt = authOptions.value.find(o =>
    ids.includes(String(o.id || '').toLowerCase())
  )
  return opt ? localize(opt.label) || localize(opt.name) : ''
}

// "Real" button = human-written option.
const realLabel = computed(() =>
  findOptionLabel('human', 'real') || t('authenticity.detail.voteReal')
)

// "Fake" button = AI/LLM-generated option.
const fakeLabel = computed(() =>
  findOptionLabel('ai', 'llm', 'fake') || t('authenticity.detail.voteFake')
)

// Emit status changes to parent
watch(currentItemStatus, (newStatus) => {
  emit('status-change', newStatus)
}, { immediate: true })

// Emit saving changes to parent
watch(saving, (isSaving) => {
  emit('saving-change', isSaving)
})

// Submit vote (auto-saves)
async function submitVote(voteValue) {
  if (!canEvaluate.value) return
  const result = await doSubmitVote(voteValue)
  if (result.success) {
    // The authenticity composable populates currentItem with `thread_id`
    // (not item_id). Emit the real id so EvaluationSession.markItemCompleted —
    // which matches on item.thread_id === id — can find the item and bump
    // progress.completed (otherwise the universal thank-you never fires).
    emit('item-completed', currentItem.value?.thread_id ?? currentItem.value?.item_id)
    if (progress.value.completed === progress.value.total) {
      emit('all-completed')
    }
  }
}

// Save metadata on confidence change
function onConfidenceChange() {
  doSaveMetadata()
}

// Save metadata on blur
function saveMetadata() {
  doSaveMetadata()
}

// -----------------------------------------------------------------------------
// Collapsible confidence + notes
// -----------------------------------------------------------------------------
// Collapsed by default so the secondary metadata doesn't crowd the vote
// buttons on mobile. Auto-expands when a previously-saved note exists for the
// loaded item so raters can see their reasoning without hunting for the toggle.
const metaExpanded = ref(false)
watch(notes, (val) => {
  if (val && !metaExpanded.value) metaExpanded.value = true
}, { immediate: true })

// -----------------------------------------------------------------------------
// Mobile fullscreen read mode (message content)
// -----------------------------------------------------------------------------
// On phones the left content panel is capped at ~40vh (≈150px), making long
// histories unreadable. The fullscreen overlay renders the same content
// (LMessageList / plain text) full-height. Read-only — desktop never shows the
// trigger (v-if="isMobile"). Closes automatically when the item changes so a
// stale history isn't shown after navigation.
const fullscreenOpen = ref(false)

function openFullscreen() {
  fullscreenOpen.value = true
}

watch(currentItem, () => {
  fullscreenOpen.value = false
})

// Initialize on mount
onMounted(async () => {
  await loadItems()
  // Navigate to initial item if specified
  if (props.initialItemId && items.value.length > 0) {
    const targetItemId = Number(props.initialItemId)
    const targetIndex = items.value.findIndex(item =>
      (item.thread_id || item.id || item.item_id) === targetItemId
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

// Watch for initialItemId changes (e.g., when navigating between items via URL)
watch(() => props.initialItemId, async (newItemId) => {
  if (newItemId && items.value.length > 0) {
    const targetItemId = Number(newItemId)
    // Check if this item is already the current item
    const currentId = currentItem.value?.thread_id || currentItem.value?.id || currentItem.value?.item_id
    if (currentId === targetItemId) return // Already on this item

    const targetIndex = items.value.findIndex(item =>
      (item.thread_id || item.id || item.item_id) === targetItemId
    )
    if (targetIndex >= 0 && targetIndex !== currentItemIndex.value) {
      const item = items.value[targetIndex]
      await loadItem(item.thread_id || item.id || item.item_id)
    }
  }
})
</script>

<style scoped>
.authenticity-interface {
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
  color: rgb(var(--v-theme-on-surface));
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

/* Info Box */
.info-box {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  background: rgba(136, 196, 200, 0.1);
  border: 1px solid rgba(136, 196, 200, 0.3);
  border-radius: 10px 3px 10px 3px;
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
  border-radius: 12px 3px 12px 3px;
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

.vote-label {
  font-size: 1.1rem;
  font-weight: 600;
}

.vote-hint {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Real Vote Button - LLARS Success */
.vote-real {
  border-color: rgba(152, 212, 187, 0.4);
}

.vote-real:hover:not(:disabled) {
  background: rgba(152, 212, 187, 0.15);
  border-color: var(--llars-success, #98d4bb);
}

.vote-real.selected {
  background: rgba(152, 212, 187, 0.2);
  border-color: var(--llars-success, #98d4bb);
  box-shadow: 0 0 0 3px rgba(152, 212, 187, 0.25);
}

/* Fake Vote Button - LLARS Danger */
.vote-fake {
  border-color: rgba(232, 160, 135, 0.4);
}

.vote-fake:hover:not(:disabled) {
  background: rgba(232, 160, 135, 0.15);
  border-color: var(--llars-danger, #e8a087);
}

.vote-fake.selected {
  background: rgba(232, 160, 135, 0.2);
  border-color: var(--llars-danger, #e8a087);
  box-shadow: 0 0 0 3px rgba(232, 160, 135, 0.25);
}

/* Collapsible metadata group (confidence + notes) */
.metadata-group {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  padding-top: 8px;
}

.metadata-toggle {
  display: flex;
  align-items: center;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 0;
  min-height: 38px;
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  transition: color 0.15s ease;
}

.metadata-toggle:hover {
  color: rgba(var(--v-theme-on-surface), 0.95);
}

.metadata-hint {
  margin-left: 6px;
  font-size: 0.78rem;
  font-weight: 400;
  font-style: italic;
  color: rgba(var(--v-theme-on-surface), 0.5);
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

/* Mobile fullscreen read overlay — mirrors ComparisonInterface's
   .option-fullscreen pattern (top bar + scrollable content). Only the
   message history is shown; voting stays in the right panel. */
.content-fullscreen {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: rgb(var(--v-theme-surface));
}

.content-fullscreen-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  background: rgba(var(--v-theme-surface-variant), 0.4);
  flex-shrink: 0;
}

.content-fullscreen-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.content-fullscreen-content {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 14px calc(16px + env(safe-area-inset-bottom, 0px));
}

/* Slim mobile fullscreen trigger row over the content panel. */
.content-panel-header {
  min-height: 44px;
}

/* Responsive */
@media (max-width: 768px) {
  .authenticity-interface {
    flex-direction: column;
  }

  .left-panel,
  .right-panel {
    width: 100% !important;
  }

  .left-panel {
    max-height: 40vh;
    border-right: none;
    border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  }

  /* Bound the right panel so an auto-growing notes textarea can't push the
     vote buttons off-screen. The .panel-content inside already scrolls. */
  .right-panel {
    max-height: 60vh;
  }

  .resize-handle {
    display: none;
  }

  .vote-buttons {
    flex-direction: column;
  }
}

/* Phones: shrink secondary chrome so the vote buttons + content get the room.
   (Steigerwald 2026-06-05) Panel headers shrink, padding compresses, the info
   box slims down, and the vote hint grows to stay ≥12px legible. */
@media (max-width: 600px) {
  .panel-header {
    padding: 6px 10px;
  }

  .panel-header h3 {
    font-size: 0.85rem;
  }

  .panel-content {
    padding: 8px;
  }

  .info-box {
    padding: 8px 10px;
    margin-bottom: 12px;
    font-size: 0.82rem;
  }

  .vote-section {
    margin-bottom: 16px;
  }

  .section-title {
    font-size: 0.95rem;
    margin-bottom: 8px;
  }

  .vote-btn {
    padding: 14px 12px;
  }

  /* ≥12px so the hint stays legible on small screens. */
  .vote-hint {
    font-size: 0.85rem;
  }

  .nav-footer {
    padding: 8px 10px;
  }
}
</style>
