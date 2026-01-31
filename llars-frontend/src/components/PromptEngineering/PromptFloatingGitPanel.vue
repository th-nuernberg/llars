<!--
  PromptFloatingGitPanel.vue

  Floating draggable Git panel for Prompt Engineering.
  Shows block-level changes like LaTeX shows file-level changes.
  Uses LFloatingWindow for consistent LLARS design.
-->
<template>
  <LFloatingWindow
    :model-value="modelValue"
    :title="$t('promptEngineering.floatingGit.title')"
    icon="mdi-source-branch"
    color="primary"
    :width="680"
    :height="500"
    :min-width="500"
    :min-height="350"
    storage-key="llars-prompt-git-panel"
    :show-close="true"
    :show-refresh="true"
    :refresh-loading="loadingChanges"
    :refresh-tooltip="$t('common.refresh')"
    @update:model-value="$emit('update:modelValue', $event)"
    @refresh="refresh"
    @close="$emit('update:modelValue', false)"
  >
    <!-- Status Tags -->
    <template #tags>
      <LTag v-if="hasChanges" variant="warning" size="small">
        +{{ totalInsertions }} / -{{ totalDeletions }}
      </LTag>
      <LTag v-else variant="success" size="small">
        {{ $t('promptEngineering.floatingGit.synced') }}
      </LTag>
    </template>

    <!-- Content -->
    <div class="git-panel-content">
      <v-alert v-if="loadError" type="error" variant="tonal" class="mb-3" density="compact">
        {{ loadError }}
      </v-alert>

      <!-- Tabs -->
      <LTabs v-model="activeTab" :tabs="tabs" class="mb-3" />

      <!-- Changes Tab -->
      <div v-if="activeTab === 'changes'" class="tab-content">
        <div class="content-grid">
          <!-- Left: Block List -->
          <div class="block-list-section">
            <div class="section-header">
              <LIcon size="16" class="mr-1">mdi-file-document-multiple</LIcon>
              {{ $t('promptEngineering.floatingGit.blocks') }}
              <v-spacer />
              <span class="block-count">{{ selectedBlocks.length }}/{{ changedBlocks.length }}</span>
            </div>

            <v-skeleton-loader v-if="loadingChanges" type="list-item@4" />
            <div v-else-if="changedBlocks.length === 0" class="empty-state">
              <LIcon size="36" class="mb-2">mdi-check-circle</LIcon>
              <span>{{ $t('promptEngineering.floatingGit.noChanges') }}</span>
            </div>
            <div v-else>
              <!-- Bulk Actions -->
              <div class="bulk-actions">
                <LBtn variant="text" size="small" @click="selectAllBlocks">
                  {{ $t('promptEngineering.floatingGit.selectAll') }}
                </LBtn>
                <LBtn variant="text" size="small" @click="deselectAllBlocks">
                  {{ $t('promptEngineering.floatingGit.selectNone') }}
                </LBtn>
              </div>

              <!-- Block List -->
              <div class="block-list">
                <div
                  v-for="block in changedBlocks"
                  :key="block.id"
                  class="block-item"
                  :class="{
                    selected: selectedBlocks.includes(block.id),
                    'diff-active': selectedDiffBlock === block.id
                  }"
                  @click="selectBlockForDiff(block)"
                >
                  <LCheckbox
                    :model-value="selectedBlocks.includes(block.id)"
                    size="small"
                    class="block-checkbox"
                    @click.stop
                    @update:model-value="toggleBlock(block.id)"
                  />
                  <!-- Status Badge -->
                  <v-tooltip location="top">
                    <template #activator="{ props: tp }">
                      <span v-bind="tp" class="status-badge" :class="getStatusClass(block.status)">
                        {{ block.status }}
                      </span>
                    </template>
                    <span>{{ getStatusTooltip(block.status) }}</span>
                  </v-tooltip>
                  <LIcon size="16">mdi-text-box</LIcon>
                  <div class="block-details">
                    <div class="block-title">{{ block.title }}</div>
                    <div class="block-stats">
                      <span class="stat-badge success">+{{ block.insertions }}</span>
                      <span class="stat-badge error">-{{ block.deletions }}</span>
                    </div>
                  </div>
                  <!-- Rollback Button -->
                  <v-tooltip v-if="block.has_baseline" location="left">
                    <template #activator="{ props: tp }">
                      <v-btn
                        v-bind="tp"
                        icon
                        variant="tonal"
                        size="x-small"
                        color="warning"
                        :loading="rollingBackBlock === block.id"
                        @click.stop="confirmBlockRollback(block)"
                      >
                        <LIcon size="14">mdi-undo</LIcon>
                      </v-btn>
                    </template>
                    <span>{{ $t('promptEngineering.floatingGit.discardChanges') }}</span>
                  </v-tooltip>
                </div>
              </div>
            </div>
          </div>

          <!-- Right: Diff Viewer -->
          <div class="diff-section">
            <div class="section-header">
              <LIcon size="16" class="mr-1">mdi-file-compare</LIcon>
              {{ $t('promptEngineering.floatingGit.diff') }}
            </div>

            <div v-if="!selectedDiffBlock" class="empty-state">
              <LIcon size="36" class="mb-2">mdi-file-document-outline</LIcon>
              <span>{{ $t('promptEngineering.floatingGit.selectBlock') }}</span>
            </div>
            <v-skeleton-loader v-else-if="loadingDiff" type="table" height="200" />
            <v-alert v-else-if="diffError" type="error" variant="tonal" density="compact">
              {{ diffError }}
            </v-alert>
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

      <!-- History Tab -->
      <div v-if="activeTab === 'history'" class="tab-content">
        <div class="content-grid">
          <!-- Left: Commit List -->
          <div class="block-list-section">
            <div class="section-header">
              <LIcon size="16" class="mr-1">mdi-source-commit</LIcon>
              {{ $t('promptEngineering.floatingGit.commits') }}
              <v-spacer />
              <span class="block-count">{{ commits.length }}</span>
            </div>

            <v-skeleton-loader v-if="loadingCommits" type="list-item@6" />
            <div v-else-if="commits.length === 0" class="empty-state">
              <LIcon size="36" class="mb-2">mdi-source-commit</LIcon>
              <span>{{ $t('promptEngineering.floatingGit.noCommits') }}</span>
            </div>
            <div v-else class="history-list">
              <div
                v-for="(c, idx) in commits"
                :key="c.id"
                class="history-item"
                :class="{ 'diff-active': selectedCommit?.id === c.id }"
                @click="selectCommitForDiff(c, idx)"
              >
                <div class="commit-indicator" />
                <div class="commit-details">
                  <div class="commit-message">{{ c.message }}</div>
                  <div class="commit-meta">
                    <span class="author">{{ c.author }}</span>
                    <span class="date">{{ formatDate(c.created_at) }}</span>
                  </div>
                </div>
                <LTag variant="gray" size="small">#{{ c.id }}</LTag>
              </div>
            </div>
          </div>

          <!-- Right: Commit Diff View -->
          <div class="diff-section">
            <div class="section-header">
              <LIcon size="16" class="mr-1">mdi-file-compare</LIcon>
              {{ $t('promptEngineering.floatingGit.commitChanges') }}
              <span v-if="selectedCommit" class="diff-file-name">#{{ selectedCommit.id }}</span>
            </div>

            <div v-if="!selectedCommit" class="empty-state">
              <LIcon size="36" class="mb-2">mdi-source-commit</LIcon>
              <span>{{ $t('promptEngineering.floatingGit.selectCommit') }}</span>
            </div>
            <v-skeleton-loader v-else-if="loadingCommitDiff" type="table" height="200" />
            <v-alert v-else-if="commitDiffError" type="error" variant="tonal" density="compact">
              {{ commitDiffError }}
            </v-alert>
            <div v-else class="commit-diff-content">
              <!-- Block changes in this commit -->
              <div v-if="commitDiffBlocks.length === 0" class="empty-state">
                <LIcon size="36" class="mb-2">mdi-check-circle</LIcon>
                <span>{{ $t('promptEngineering.floatingGit.noBlockChanges') }}</span>
              </div>
              <div v-else class="commit-blocks-list">
                <div
                  v-for="block in commitDiffBlocks"
                  :key="block.title"
                  class="commit-block-item"
                  :class="{ 'diff-active': selectedCommitBlock === block.title }"
                  @click="selectCommitBlock(block)"
                >
                  <span class="status-badge" :class="getStatusClass(block.status)">
                    {{ block.status }}
                  </span>
                  <span class="block-title">{{ block.title }}</span>
                  <span class="block-stats">
                    <span class="stat-badge success">+{{ block.insertions }}</span>
                    <span class="stat-badge error">-{{ block.deletions }}</span>
                  </span>
                </div>
              </div>
              <!-- Diff Viewer for selected block -->
              <div v-if="selectedCommitBlock" class="commit-block-diff">
                <div class="diff-header">
                  <LIcon size="14">mdi-file-document</LIcon>
                  {{ selectedCommitBlock }}
                </div>
                <DiffViewer
                  :base-text="commitBlockDiffBase"
                  :compare-text="commitBlockDiffCompare"
                  :base-label="commitBlockDiffBaseLabel"
                  :compare-label="commitBlockDiffCompareLabel"
                  class="diff-viewer"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer: Commit -->
    <template #footer>
      <v-text-field
        v-model="commitMessage"
        :placeholder="$t('promptEngineering.floatingGit.commitPlaceholder')"
        variant="outlined"
        density="compact"
        :disabled="!hasChanges"
        hide-details
        class="commit-input"
        @keyup.enter="submitCommit"
      />
      <LBtn
        variant="primary"
        size="small"
        :loading="committing"
        :disabled="!canCommit"
        prepend-icon="mdi-check"
        @click="submitCommit"
      >
        {{ $t('promptEngineering.floatingGit.commit') }}
      </LBtn>
    </template>
  </LFloatingWindow>

  <!-- Rollback Confirmation Dialog -->
  <v-dialog v-model="showRollbackConfirm" max-width="400" persistent>
    <LCard>
      <template #header>
        <div class="d-flex align-center w-100">
          <LIcon class="mr-2" color="warning">mdi-alert-circle</LIcon>
          <span class="text-h6">{{ $t('promptEngineering.floatingGit.rollbackTitle') }}</span>
        </div>
      </template>

      <p>
        <i18n-t keypath="promptEngineering.floatingGit.rollbackConfirm" tag="span">
          <template #name>
            <strong>{{ rollbackTarget?.title }}</strong>
          </template>
        </i18n-t>
      </p>
      <p class="text-medium-emphasis mt-2 mb-0">
        {{ $t('promptEngineering.floatingGit.rollbackHint') }}
      </p>

      <template #actions>
        <v-spacer />
        <LBtn variant="cancel" @click="cancelRollback">{{ $t('common.cancel') }}</LBtn>
        <LBtn variant="danger" prepend-icon="mdi-undo" @click="executeBlockRollback">
          {{ $t('promptEngineering.floatingGit.rollbackAction') }}
        </LBtn>
      </template>
    </LCard>
  </v-dialog>
</template>

<script setup>
/**
 * PromptFloatingGitPanel - Git Panel for Prompt Engineering
 *
 * Displays block-level changes for prompt templates using the
 * global LFloatingWindow component for consistent LLARS design.
 *
 * Features:
 * - Block-level change tracking (like files in LaTeX)
 * - Side-by-side diff viewer
 * - Commit history
 * - Block rollback functionality
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useI18n } from 'vue-i18n'
import { DiffViewer } from '@/components/common/Git'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const props = defineProps({
  /** v-model for panel visibility */
  modelValue: { type: Boolean, default: false },
  /** ID of the prompt to show changes for */
  promptId: { type: Number, required: true },
  /** Function to get current content for commit snapshot */
  getContent: { type: Function, default: null },
  /** Summary object with change statistics */
  summary: {
    type: Object,
    default: () => ({
      users: [],
      totalChangedLines: 0,
      hasChanges: false,
      insertions: 0,
      deletions: 0
    })
  }
})

const emit = defineEmits(['update:modelValue', 'committed', 'rollback'])
const { t, locale } = useI18n()

// Tab state
const activeTab = ref('changes')
const tabs = computed(() => [
  { value: 'changes', label: t('promptEngineering.floatingGit.tabChanges') },
  { value: 'history', label: t('promptEngineering.floatingGit.tabHistory') }
])

// Changes state
const changedBlocks = ref([])
const selectedBlocks = ref([])
const loadingChanges = ref(false)
const loadError = ref('')

// Diff state
const selectedDiffBlock = ref(null)
const diffBaseText = ref('')
const diffCompareText = ref('')
const diffBaseLabel = ref('')
const diffCompareLabel = ref('')
const diffError = ref('')
const loadingDiff = ref(false)

// Commit state
const commits = ref([])
const loadingCommits = ref(false)
const commitMessage = ref('')
const committing = ref(false)
const commitError = ref('')

// Rollback state
const showRollbackConfirm = ref(false)
const rollbackTarget = ref(null)
const rollingBackBlock = ref(null)

// Commit history diff state
const selectedCommit = ref(null)
const selectedCommitIndex = ref(-1)
const loadingCommitDiff = ref(false)
const commitDiffError = ref('')
const commitDiffBlocks = ref([])
const selectedCommitBlock = ref(null)
const commitBlockDiffBase = ref('')
const commitBlockDiffCompare = ref('')
const commitBlockDiffBaseLabel = ref('')
const commitBlockDiffCompareLabel = ref('')

// Computed
const hasChanges = computed(() =>
  changedBlocks.value.length > 0 || props.summary?.hasChanges
)

const totalInsertions = computed(() =>
  changedBlocks.value.reduce((sum, b) => sum + (b.insertions || 0), 0) ||
  props.summary?.insertions ||
  0
)

const totalDeletions = computed(() =>
  changedBlocks.value.reduce((sum, b) => sum + (b.deletions || 0), 0) ||
  props.summary?.deletions ||
  0
)

const canCommit = computed(() =>
  commitMessage.value.trim().length > 0 && hasChanges.value
)

// Helpers
function authHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function formatDate(iso) {
  if (!iso) return ''
  try {
    const date = new Date(iso)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return t('promptEngineering.floatingGit.justNow')
    if (diffMins < 60) return t('promptEngineering.floatingGit.minutesAgo', { count: diffMins })
    if (diffHours < 24) return t('promptEngineering.floatingGit.hoursAgo', { count: diffHours })
    if (diffDays < 7) return t('promptEngineering.floatingGit.daysAgo', { count: diffDays })
    return new Intl.DateTimeFormat(locale.value || 'en', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit'
    }).format(date)
  } catch {
    return iso
  }
}

function getStatusClass(status) {
  switch (status) {
    case 'A': return 'info'
    case 'D': return 'error'
    case 'M': return 'warning'
    default: return 'grey'
  }
}

function getStatusTooltip(status) {
  switch (status) {
    case 'A': return t('promptEngineering.floatingGit.statusAdded')
    case 'D': return t('promptEngineering.floatingGit.statusDeleted')
    case 'M': return t('promptEngineering.floatingGit.statusModified')
    default: return status
  }
}

// Block selection
function toggleBlock(blockId) {
  const idx = selectedBlocks.value.indexOf(blockId)
  if (idx === -1) {
    selectedBlocks.value.push(blockId)
  } else {
    selectedBlocks.value.splice(idx, 1)
  }
}

function selectAllBlocks() {
  selectedBlocks.value = changedBlocks.value.map(b => b.id)
}

function deselectAllBlocks() {
  selectedBlocks.value = []
}

function selectBlockForDiff(block) {
  selectedDiffBlock.value = block.id
  if (!selectedBlocks.value.includes(block.id)) {
    toggleBlock(block.id)
  }
  loadBlockDiff(block.id)
}

// API calls
async function loadChanges() {
  if (!props.promptId) return

  loadingChanges.value = true
  loadError.value = ''

  try {
    // Get current content from YJS state via getContent prop
    const currentContent = props.getContent ? props.getContent() : null

    // Use POST to send current content for accurate comparison
    const res = await axios.post(
      `${API_BASE}/api/prompts/${props.promptId}/changes`,
      { current_content: currentContent },
      { headers: authHeaders() }
    )
    changedBlocks.value = res.data.changed_blocks || []
    // Select all by default
    selectedBlocks.value = changedBlocks.value.map(b => b.id)
  } catch (e) {
    loadError.value = e?.response?.data?.error || e?.message || t('promptEngineering.floatingGit.loadError')
    changedBlocks.value = []
  } finally {
    loadingChanges.value = false
  }
}

async function loadBlockDiff(blockId) {
  if (!props.promptId || !blockId) return

  loadingDiff.value = true
  diffError.value = ''

  try {
    // Get current content from YJS state via getContent prop
    const currentContent = props.getContent ? props.getContent() : null

    // Use POST to send current content for accurate diff
    const res = await axios.post(
      `${API_BASE}/api/prompts/${props.promptId}/blocks/${encodeURIComponent(blockId)}/diff`,
      { current_content: currentContent },
      { headers: authHeaders() }
    )
    diffBaseText.value = res.data.baseline_text || ''
    diffCompareText.value = res.data.current_text || ''
    diffBaseLabel.value = res.data.baseline_commit_id
      ? `#${res.data.baseline_commit_id}`
      : t('promptEngineering.floatingGit.initial')
    diffCompareLabel.value = t('promptEngineering.floatingGit.current')
  } catch (e) {
    diffError.value = e?.response?.data?.error || e?.message || t('promptEngineering.floatingGit.diffError')
  } finally {
    loadingDiff.value = false
  }
}

async function loadCommits() {
  if (!props.promptId) return

  loadingCommits.value = true

  try {
    const res = await axios.get(
      `${API_BASE}/api/prompts/${props.promptId}/commits`,
      { headers: authHeaders() }
    )
    commits.value = res.data.commits || []
  } catch (e) {
    commits.value = []
  } finally {
    loadingCommits.value = false
  }
}

async function submitCommit() {
  if (!canCommit.value) return

  committing.value = true
  commitError.value = ''

  try {
    const contentSnapshot = props.getContent ? props.getContent() : null

    await axios.post(
      `${API_BASE}/api/prompts/${props.promptId}/commit`,
      {
        message: commitMessage.value.trim(),
        diff_summary: props.summary || null,
        content_snapshot: contentSnapshot
      },
      { headers: authHeaders() }
    )

    commitMessage.value = ''
    await refresh()
    emit('committed')
  } catch (e) {
    commitError.value = e?.response?.data?.error || e?.message || t('promptEngineering.floatingGit.commitError')
  } finally {
    committing.value = false
  }
}

function confirmBlockRollback(block) {
  rollbackTarget.value = block
  showRollbackConfirm.value = true
}

function cancelRollback() {
  rollbackTarget.value = null
  showRollbackConfirm.value = false
}

async function executeBlockRollback() {
  if (!rollbackTarget.value) return

  const block = rollbackTarget.value
  rollingBackBlock.value = block.id
  showRollbackConfirm.value = false

  try {
    await axios.post(
      `${API_BASE}/api/prompts/${props.promptId}/rollback`,
      { block_id: block.id },
      { headers: authHeaders() }
    )

    await refresh()
    emit('rollback', { blockId: block.id })
  } catch (e) {
    loadError.value = e?.response?.data?.error || e?.message || t('promptEngineering.floatingGit.rollbackError')
  } finally {
    rollingBackBlock.value = null
    rollbackTarget.value = null
  }
}

// Commit history diff functions
async function selectCommitForDiff(commit, index) {
  selectedCommit.value = commit
  selectedCommitIndex.value = index
  selectedCommitBlock.value = null
  commitBlockDiffBase.value = ''
  commitBlockDiffCompare.value = ''
  await loadCommitDiff(commit.id, index)
}

async function loadCommitDiff(commitId, index) {
  loadingCommitDiff.value = true
  commitDiffError.value = ''
  commitDiffBlocks.value = []

  try {
    const res = await axios.get(
      `${API_BASE}/api/prompts/${props.promptId}/commits/${commitId}/diff`,
      { headers: authHeaders() }
    )
    commitDiffBlocks.value = res.data.changed_blocks || []

    // Auto-select first block if available
    if (commitDiffBlocks.value.length > 0) {
      selectCommitBlock(commitDiffBlocks.value[0])
    }
  } catch (e) {
    commitDiffError.value = e?.response?.data?.error || e?.message || t('promptEngineering.floatingGit.diffError')
    commitDiffBlocks.value = []
  } finally {
    loadingCommitDiff.value = false
  }
}

function selectCommitBlock(block) {
  selectedCommitBlock.value = block.title
  commitBlockDiffBase.value = block.before || ''
  commitBlockDiffCompare.value = block.after || ''

  // Set labels based on commit context
  const prevCommit = commits.value[selectedCommitIndex.value + 1]
  commitBlockDiffBaseLabel.value = prevCommit
    ? `#${prevCommit.id}`
    : t('promptEngineering.floatingGit.initial')
  commitBlockDiffCompareLabel.value = `#${selectedCommit.value.id}`
}

async function refresh() {
  await Promise.all([loadChanges(), loadCommits()])
  if (selectedDiffBlock.value) {
    await loadBlockDiff(selectedDiffBlock.value)
  }
}

// Watchers
watch(() => props.modelValue, async (isOpen) => {
  if (isOpen) {
    await refresh()
  }
})

watch(() => props.promptId, async (newId, oldId) => {
  if (newId !== oldId && props.modelValue) {
    await refresh()
  }
})
</script>

<style scoped>
/* Content Layout */
.git-panel-content {
  padding: 12px;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tab-content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.history-tab {
  overflow-y: auto;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.section-header {
  font-weight: 600;
  font-size: 12px;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 8px;
  display: flex;
  align-items: center;
}

.block-count {
  font-weight: 400;
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Block List */
.block-list-section {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.bulk-actions {
  display: flex;
  gap: 4px;
  justify-content: flex-end;
  margin-bottom: 6px;
}

.block-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.block-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s;
}

.block-item:hover {
  background: rgba(var(--v-theme-primary), 0.05);
}

.block-item.selected {
  background: rgba(var(--v-theme-primary), 0.12);
}

.block-item.diff-active {
  border-left: 3px solid var(--llars-accent, #88c4c8);
  background: rgba(var(--v-theme-accent), 0.15);
}

.block-checkbox {
  flex-shrink: 0;
}

.block-details {
  flex: 1;
  min-width: 0;
}

.block-title {
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.block-stats {
  display: flex;
  gap: 4px;
  margin-top: 2px;
}

.stat-badge {
  font-size: 10px;
  font-family: monospace;
  padding: 1px 4px;
  border-radius: 3px;
}

.stat-badge.success {
  background: rgba(152, 212, 187, 0.2);
  color: #2e7d32;
}

.stat-badge.error {
  background: rgba(232, 160, 135, 0.2);
  color: #c62828;
}

/* Status Badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  font-size: 9px;
  font-weight: 700;
  border-radius: 3px;
  flex-shrink: 0;
}

.status-badge.warning {
  background: rgba(232, 200, 122, 0.25);
  color: #f9a825;
}

.status-badge.info {
  background: rgba(136, 196, 200, 0.25);
  color: #0288d1;
}

.status-badge.error {
  background: rgba(232, 160, 135, 0.25);
  color: #c62828;
}

/* Diff Section */
.diff-section {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.diff-viewer {
  flex: 1;
  min-height: 0;
}

/* History */
.history-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  overflow-y: auto;
  padding: 4px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 4px;
  transition: background 0.15s;
  cursor: pointer;
}

.history-item:hover {
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.history-item.diff-active {
  background: rgba(var(--v-theme-primary), 0.12);
  border-left: 3px solid var(--llars-accent, #88c4c8);
}

.commit-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--llars-primary, #b0ca97);
  flex-shrink: 0;
}

.commit-details {
  flex: 1;
  min-width: 0;
}

.commit-message {
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.commit-meta {
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  display: flex;
  gap: 6px;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-size: 12px;
  flex: 1;
}

.empty-state :deep(.v-icon) {
  color: rgba(var(--v-theme-on-surface), 0.4) !important;
}

/* Footer */
.commit-input {
  flex: 1;
}

.commit-input :deep(.v-field) {
  border-radius: 8px 2px 8px 2px !important;
}

.w-100 {
  width: 100%;
}

/* Commit Diff Content */
.commit-diff-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.commit-blocks-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px;
  max-height: 120px;
  overflow-y: auto;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.commit-block-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.15s;
}

.commit-block-item:hover {
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.commit-block-item.diff-active {
  background: rgba(var(--v-theme-primary), 0.12);
  border-left: 3px solid var(--llars-accent, #88c4c8);
}

.commit-block-item .block-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.commit-block-item .block-stats {
  display: flex;
  gap: 4px;
}

.commit-block-diff {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.commit-block-diff .diff-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  font-size: 11px;
  font-weight: 600;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.commit-block-diff .diff-viewer {
  flex: 1;
  min-height: 0;
}
</style>
