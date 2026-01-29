<!--
  FloatingGitPanel.vue

  A draggable floating window for Git operations.
  Similar to the floating comment card and AI stream window.
-->
<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      ref="floatingPanelRef"
      class="floating-git-panel"
      :style="panelStyle"
    >
      <!-- Draggable Header -->
      <div
        class="floating-git-header"
        @mousedown="startDrag"
      >
        <div class="git-header-left">
          <LIcon size="18" color="primary">mdi-source-branch</LIcon>
          <span class="floating-git-title">{{ $t('workspaceGit.fullscreen.title') }}</span>
        </div>
        <div class="git-header-tags">
          <LTag v-if="changedCount > 0" variant="warning" size="x-small">
            {{ changedCount }} {{ $t('workspaceGit.tags.changed', { count: changedCount }) }}
          </LTag>
          <LTag v-if="deletedCount > 0" variant="danger" size="x-small">
            {{ deletedCount }} {{ $t('workspaceGit.tags.deleted', { count: deletedCount }) }}
          </LTag>
          <LTag v-if="changedCount === 0 && deletedCount === 0" variant="success" size="x-small">
            {{ $t('workspaceGit.tags.synced') }}
          </LTag>
        </div>
        <v-spacer />
        <LIconBtn
          icon="mdi-refresh"
          size="x-small"
          :tooltip="$t('workspaceGit.actions.refresh')"
          :loading="checkingChanges"
          @click="refresh"
        />
        <LIconBtn
          icon="mdi-close"
          size="x-small"
          :tooltip="$t('common.close')"
          @click="$emit('update:modelValue', false)"
        />
      </div>

      <!-- Content -->
      <div class="floating-git-content">
        <!-- Two Column Layout -->
        <div class="git-columns">
          <!-- Left: Files List -->
          <div class="git-column git-files-column">
            <div class="column-header">
              <LIcon size="14">mdi-file-document-multiple</LIcon>
              <span>{{ $t('workspaceGit.files.title') }}</span>
              <span class="file-count">({{ selectedFiles.length }}/{{ changedCount + deletedCount }})</span>
            </div>
            <div class="column-content">
              <!-- Select All -->
              <div v-if="changedCount + deletedCount > 0" class="select-all-row">
                <LCheckbox
                  :model-value="allSelected"
                  size="x-small"
                  @update:model-value="$event ? selectAll() : deselectAll()"
                />
                <span class="select-all-label">{{ $t('workspaceGit.files.selectAll') }}</span>
              </div>

              <!-- Changed Files -->
              <div
                v-for="file in changedFiles"
                :key="file.id"
                class="file-row"
                :class="{ selected: selectedDiffFile?.id === file.id }"
                @click="selectFileForDiff(file)"
              >
                <LCheckbox
                  :model-value="selectedFiles.includes(file.id)"
                  size="x-small"
                  @update:model-value="toggleFile(file.id)"
                  @click.stop
                />
                <LIcon size="14" :color="getFileIconColor(file.path)">
                  {{ getFileIcon(file.path) }}
                </LIcon>
                <span class="file-name">{{ file.title || file.path }}</span>
                <LTag :variant="getStatusBadge(file).color" size="x-small">
                  {{ getStatusBadge(file).text }}
                </LTag>
                <span class="file-stats">
                  <span class="stat-add">+{{ file.insertions || 0 }}</span>
                  <span class="stat-del">-{{ file.deletions || 0 }}</span>
                </span>
              </div>

              <!-- Deleted Files -->
              <div
                v-for="file in deletedFiles"
                :key="`del-${file.id}`"
                class="file-row deleted"
              >
                <LCheckbox
                  :model-value="selectedFiles.includes(`del-${file.id}`)"
                  size="x-small"
                  @update:model-value="toggleFile(`del-${file.id}`)"
                  @click.stop
                />
                <LIcon size="14" color="error">mdi-file-remove</LIcon>
                <span class="file-name deleted-name">{{ file.title }}</span>
                <LTag variant="danger" size="x-small">D</LTag>
              </div>

              <!-- Empty State -->
              <div v-if="changedCount === 0 && deletedCount === 0" class="empty-state">
                <LIcon size="24" class="text-medium-emphasis">mdi-check-circle</LIcon>
                <span>{{ $t('workspaceGit.files.empty') }}</span>
              </div>
            </div>
          </div>

          <!-- Right: Diff View -->
          <div class="git-column git-diff-column">
            <div class="column-header">
              <LIcon size="14">mdi-file-compare</LIcon>
              <span>{{ $t('workspaceGit.diff.title') }}</span>
              <span v-if="selectedDiffFile" class="diff-file-name">{{ selectedDiffFile.path }}</span>
            </div>
            <div class="column-content diff-content">
              <div v-if="!selectedDiffFile" class="empty-state">
                <LIcon size="24" class="text-medium-emphasis">mdi-file-document-outline</LIcon>
                <span>{{ $t('workspaceGit.diff.selectFile') }}</span>
              </div>
              <div v-else-if="loadingDiff" class="loading-state">
                <v-progress-circular indeterminate size="24" width="2" />
                <span>{{ $t('workspaceGit.diff.loading') }}</span>
              </div>
              <DiffViewer
                v-else
                :base-text="diffBaseText"
                :compare-text="diffCompareText"
                :base-label="diffBaseLabel"
                :compare-label="diffCompareLabel"
                class="diff-viewer"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Footer: Commit -->
      <div class="floating-git-footer">
        <v-text-field
          v-model="commitMessage"
          :placeholder="$t('workspaceGit.commit.placeholder')"
          density="compact"
          variant="outlined"
          hide-details
          class="commit-input"
          @keyup.enter="handleCommit"
        />
        <LBtn
          variant="primary"
          size="small"
          :loading="committing"
          :disabled="!canCommit"
          @click="handleCommit"
        >
          {{ $t('workspaceGit.commit.submit') }}
        </LBtn>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, toRef, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { useGitStatus } from '@/composables/useGitStatus'
import DiffViewer from '@/components/common/Git/DiffViewer.vue'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  workspaceId: { type: Number, required: true },
  selectedDocumentId: { type: Number, default: null },
  canCommitProp: { type: Boolean, default: false },
  apiPrefix: { type: String, default: '/api/latex-collab' },
  getContent: { type: Function, default: null }
})

const emit = defineEmits(['update:modelValue', 'committed', 'rollback', 'restored'])
const { t } = useI18n()

// Storage key for persisting position and size
const STORAGE_KEY = 'llars-git-panel-state'

// Load saved state from localStorage
function loadSavedState() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (e) {
    console.warn('[FloatingGitPanel] Failed to load saved state:', e)
  }
  return null
}

// Save state to localStorage
function saveState() {
  try {
    const panel = floatingPanelRef.value
    if (!panel) return
    const state = {
      x: panelPosition.value.x,
      y: panelPosition.value.y,
      width: panel.offsetWidth,
      height: panel.offsetHeight
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch (e) {
    console.warn('[FloatingGitPanel] Failed to save state:', e)
  }
}

// Refs
const floatingPanelRef = ref(null)
const savedState = loadSavedState()
const panelPosition = ref({
  x: savedState?.x ?? 100,
  y: savedState?.y ?? 100
})
const panelSize = ref({
  width: savedState?.width ?? 800,
  height: savedState?.height ?? 500
})
const dragOffset = ref({ x: 0, y: 0 })
const isDragging = ref(false)
const resizeObserver = ref(null)

// Diff state
const selectedDiffFile = ref(null)
const loadingDiff = ref(false)
const diffBaseText = ref('')
const diffCompareText = ref('')
const diffBaseLabel = ref('')
const diffCompareLabel = ref('')

// Git status composable
const workspaceIdRef = toRef(props, 'workspaceId')
const {
  changedFiles,
  deletedFiles,
  selectedFiles,
  checkingChanges,
  commitMessage,
  committing,
  changedCount,
  deletedCount,
  getFileIcon,
  getFileIconColor,
  getStatusBadge,
  toggleFile,
  selectAll,
  deselectAll,
  quickCommit,
  refresh
} = useGitStatus(workspaceIdRef, {
  apiPrefix: props.apiPrefix,
  autoSetup: false
})

// Computed
const panelStyle = computed(() => ({
  left: `${Math.max(10, panelPosition.value.x)}px`,
  top: `${Math.max(10, panelPosition.value.y)}px`,
  width: `${panelSize.value.width}px`,
  height: `${panelSize.value.height}px`
}))

const allSelected = computed(() => {
  const total = changedCount.value + deletedCount.value
  return total > 0 && selectedFiles.value.length === total
})

const canCommit = computed(() => {
  return props.canCommitProp && commitMessage.value.trim() && selectedFiles.value.length > 0
})

// Auth helper
function authHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// Drag functions
function startDrag(e) {
  if (e.button !== 0) return
  isDragging.value = true
  const panel = floatingPanelRef.value
  if (!panel) return
  const rect = panel.getBoundingClientRect()
  dragOffset.value = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  }
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  e.preventDefault()
}

function onDrag(e) {
  if (!isDragging.value) return
  panelPosition.value = {
    x: Math.max(0, e.clientX - dragOffset.value.x),
    y: Math.max(0, e.clientY - dragOffset.value.y)
  }
}

function stopDrag() {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  // Save position after drag
  saveState()
}

// File selection for diff
async function selectFileForDiff(file) {
  selectedDiffFile.value = file
  loadingDiff.value = true

  try {
    const res = await axios.get(
      `${API_BASE}${props.apiPrefix}/documents/${file.id}/diff`,
      { headers: authHeaders() }
    )

    diffBaseText.value = res.data?.baseline_text || ''
    diffCompareText.value = res.data?.current_text || ''
    diffBaseLabel.value = res.data?.baseline_commit_id
      ? `#${res.data.baseline_commit_id}`
      : t('workspaceGit.diff.initial')
    diffCompareLabel.value = t('workspaceGit.diff.workingTree')
  } catch (e) {
    console.error('[FloatingGitPanel] Failed to load diff:', e)
    diffBaseText.value = ''
    diffCompareText.value = ''
  } finally {
    loadingDiff.value = false
  }
}

// Commit
async function handleCommit() {
  if (!canCommit.value) return
  const success = await quickCommit(commitMessage.value)
  if (success) {
    commitMessage.value = ''
    emit('committed')
  }
}

// Setup ResizeObserver to track size changes
function setupResizeObserver() {
  if (resizeObserver.value) {
    resizeObserver.value.disconnect()
  }

  const panel = floatingPanelRef.value
  if (!panel) return

  resizeObserver.value = new ResizeObserver((entries) => {
    for (const entry of entries) {
      const { width, height } = entry.contentRect
      // Add border width (2px each side)
      panelSize.value = {
        width: Math.round(width + 4),
        height: Math.round(height + 4)
      }
      // Debounce save to avoid too many writes
      clearTimeout(resizeSaveTimeout)
      resizeSaveTimeout = setTimeout(saveState, 300)
    }
  })

  resizeObserver.value.observe(panel)
}

let resizeSaveTimeout = null

// Watch for open/close
watch(() => props.modelValue, async (isOpen) => {
  if (isOpen) {
    // Load saved state or use defaults
    const saved = loadSavedState()
    if (saved) {
      panelPosition.value = { x: saved.x, y: saved.y }
      panelSize.value = { width: saved.width, height: saved.height }
    } else {
      // Center the panel on first open
      panelPosition.value = {
        x: Math.max(100, (window.innerWidth - 800) / 2),
        y: Math.max(50, (window.innerHeight - 500) / 2)
      }
      panelSize.value = { width: 800, height: 500 }
    }
    await refresh()
    // Setup resize observer after panel is rendered
    await nextTick()
    setupResizeObserver()
  } else {
    selectedDiffFile.value = null
    diffBaseText.value = ''
    diffCompareText.value = ''
    // Cleanup resize observer
    if (resizeObserver.value) {
      resizeObserver.value.disconnect()
      resizeObserver.value = null
    }
  }
})

// Cleanup on unmount
onUnmounted(() => {
  if (resizeObserver.value) {
    resizeObserver.value.disconnect()
  }
  clearTimeout(resizeSaveTimeout)
})
</script>

<style scoped>
.floating-git-panel {
  position: fixed;
  z-index: 9999;
  min-width: 500px;
  min-height: 300px;
  max-width: calc(100vw - 40px);
  max-height: calc(100vh - 60px);
  background: rgb(var(--v-theme-surface));
  border: 2px solid var(--llars-primary, #b0ca97);
  border-radius: 12px;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.2), 0 4px 16px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: auto;
  resize: both;
}

/* Custom resize handle styling */
.floating-git-panel::-webkit-resizer {
  background: linear-gradient(135deg, transparent 50%, var(--llars-primary, #b0ca97) 50%);
  border-radius: 0 0 10px 0;
}

.floating-git-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.1) 0%, rgba(var(--v-theme-primary), 0.05) 100%);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  cursor: grab;
  user-select: none;
}

.floating-git-header:active {
  cursor: grabbing;
}

.git-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.floating-git-title {
  font-size: 14px;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.git-header-tags {
  display: flex;
  gap: 6px;
}

.floating-git-content {
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.git-columns {
  display: grid;
  grid-template-columns: 280px 1fr;
  height: 100%;
}

.git-column {
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.git-column:last-child {
  border-right: none;
}

.column-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.file-count {
  font-weight: 400;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.diff-file-name {
  font-weight: 400;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-left: auto;
  font-size: 11px;
}

.column-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.select-all-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  margin-bottom: 4px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.select-all-label {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.file-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.15s;
}

.file-row:hover {
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.file-row.selected {
  background: rgba(var(--v-theme-primary), 0.12);
  border-left: 2px solid rgb(var(--v-theme-primary));
}

.file-row.deleted {
  opacity: 0.7;
}

.file-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.deleted-name {
  text-decoration: line-through;
}

.file-stats {
  display: flex;
  gap: 4px;
  font-size: 10px;
  font-family: monospace;
}

.stat-add {
  color: rgb(var(--v-theme-success));
}

.stat-del {
  color: rgb(var(--v-theme-error));
}

.diff-content {
  padding: 0;
}

.diff-viewer {
  height: 100%;
}

.empty-state,
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 12px;
  height: 100%;
}

.floating-git-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.commit-input {
  flex: 1;
}

.commit-input :deep(.v-field) {
  font-size: 12px;
}

.commit-input :deep(.v-field__input) {
  padding: 6px 10px;
  min-height: 32px;
}

/* Dark mode */
.v-theme--dark .floating-git-panel {
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.5), 0 4px 16px rgba(0, 0, 0, 0.3);
}
</style>
