<!--
  GitDetailDialog.vue

  Centered modal dialog for detailed Git operations.
  Shows changed files, commit history, and diff viewer.
  Part of PyCharm-style Git UX redesign.
-->
<template>
  <v-dialog
    :model-value="modelValue"
    max-width="1000"
    scrollable
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <div class="git-detail-dialog">
      <!-- Header -->
      <div class="dialog-header">
        <div class="header-icon-box">
          <LIcon size="22" color="white">mdi-source-branch</LIcon>
        </div>
        <span class="header-title">{{ $t('workspaceGit.fullscreen.title') }}</span>
        <template v-if="entityMode === 'single'">
          <LTag v-if="displayHasChanges" variant="warning" size="small">
            +{{ displayInsertions }} / -{{ displayDeletions }}
          </LTag>
          <LTag v-else variant="success" size="small">
            {{ $t('workspaceGit.tags.synced') }}
          </LTag>
        </template>
        <template v-else>
          <LTag v-if="changedCount > 0" variant="warning" size="small">
            {{ $t('workspaceGit.fullscreen.changedCount', { count: changedCount }) }}
          </LTag>
          <LTag v-if="deletedCount > 0" variant="danger" size="small">
            {{ $t('workspaceGit.tags.deleted', { count: deletedCount }) }}
          </LTag>
        </template>
        <v-spacer />
        <LBtn
          variant="text"
          size="small"
          prepend-icon="mdi-refresh"
          :loading="checkingChanges"
          :title="$t('workspaceGit.actions.refresh')"
          @click="refresh"
        >
          {{ $t('common.refresh') }}
        </LBtn>
        <LIconBtn
          icon="mdi-close"
          size="small"
          :tooltip="$t('common.close')"
          class="ml-2"
          @click="$emit('update:modelValue', false)"
        />
      </div>

      <!-- Content -->
      <div class="dialog-content">
        <v-alert v-if="loadError" type="error" variant="tonal" class="mb-4">
          {{ loadError }}
        </v-alert>

        <div class="content-grid" :class="{ 'single-mode': entityMode === 'single' }">
          <!-- Left Column: Changed Files + Commit (workspace) OR just Commit (single) -->
          <div class="grid-left">
            <!-- Changed Files Card (Workspace Mode Only) -->
            <div v-if="entityMode === 'workspace'" class="git-card">
              <div class="card-header">
                <LIcon size="18" class="mr-2">mdi-file-document-multiple</LIcon>
                {{ $t('workspaceGit.files.title') }}
                <v-spacer />
                <span class="file-count">{{ selectedFiles.length }}/{{ changedCount }}</span>
              </div>
              <div class="card-content">
                <v-skeleton-loader v-if="checkingChanges" type="list-item@4" />
                <div v-else-if="changedCount === 0 && deletedCount === 0" class="empty-state">
                  <LIcon size="40" color="grey-lighten-1" class="mb-2">mdi-check-circle</LIcon>
                  <span>{{ $t('workspaceGit.files.emptyUncommitted') }}</span>
                </div>
                <div v-else>
                  <!-- Bulk Actions -->
                  <div v-if="changedCount > 0" class="bulk-actions">
                    <LBtn variant="text" size="small" @click="selectAll">
                      {{ $t('workspaceGit.files.selectAll') }}
                    </LBtn>
                    <LBtn variant="text" size="small" @click="deselectAll">
                      {{ $t('workspaceGit.files.selectNone') }}
                    </LBtn>
                  </div>

                  <v-divider v-if="changedCount > 0" class="my-2" />

                  <!-- Changed Files List -->
                  <transition-group name="file-list" tag="div" class="file-list">
                    <div
                      v-for="file in changedFiles"
                      :key="file.id"
                      class="file-item"
                      :class="{ selected: selectedFiles.includes(file.id) }"
                      @click="toggleFile(file.id)"
                    >
                      <v-checkbox
                        :model-value="selectedFiles.includes(file.id)"
                        density="compact"
                        hide-details
                        @click.stop
                        @update:model-value="toggleFile(file.id)"
                      />
                      <!-- Status Badge -->
                      <v-tooltip location="top">
                        <template #activator="{ props: tp }">
                          <span v-bind="tp" class="status-badge" :class="getStatusBadge(file).color">
                            {{ getStatusBadge(file).text }}
                          </span>
                        </template>
                        <span>{{ getStatusBadge(file).tooltip }}</span>
                      </v-tooltip>
                      <LIcon size="18" :color="getFileIconColor(file.path)">
                        {{ getFileIcon(file.path) }}
                      </LIcon>
                      <div class="file-details">
                        <div class="file-path">{{ file.path }}</div>
                        <div class="file-stats">
                          <span class="stat-badge success">+{{ file.insertions }}</span>
                          <span class="stat-badge error">-{{ file.deletions }}</span>
                        </div>
                      </div>
                      <!-- Rollback Button -->
                      <v-tooltip v-if="file.has_baseline" location="left">
                        <template #activator="{ props: tp }">
                          <v-btn
                            v-bind="tp"
                            icon
                            variant="tonal"
                            size="x-small"
                            color="warning"
                            :loading="rollingBack === file.id"
                            @click.stop="confirmRollback(file)"
                          >
                            <LIcon size="16">mdi-undo</LIcon>
                          </v-btn>
                        </template>
                        <span>{{ $t('workspaceGit.actions.discard') }}</span>
                      </v-tooltip>
                    </div>
                  </transition-group>

                  <!-- Deleted Files Section -->
                  <template v-if="deletedCount > 0">
                    <v-divider v-if="changedCount > 0" class="my-3" />
                    <div class="deleted-section-title">
                      <LIcon size="14" color="error" class="mr-1">mdi-delete</LIcon>
                      {{ $t('workspaceGit.files.deletedTitle') }}
                    </div>
                    <transition-group name="file-list" tag="div" class="deleted-list">
                      <div
                        v-for="file in deletedFiles"
                        :key="'deleted-' + file.id"
                        class="deleted-item"
                      >
                        <span class="status-badge error">D</span>
                        <LIcon size="16" color="error" class="mr-2">mdi-file-remove-outline</LIcon>
                        <div class="deleted-info">
                          <span class="deleted-name">{{ file.title }}</span>
                          <span class="deleted-date">{{ formatDate(file.deleted_at) }}</span>
                        </div>
                        <v-tooltip location="left">
                          <template #activator="{ props: tp }">
                            <v-btn
                              v-bind="tp"
                              icon
                              variant="tonal"
                              size="x-small"
                              color="success"
                              :loading="restoringFile === file.id"
                              @click.stop="handleRestoreFile(file)"
                            >
                              <LIcon size="14">mdi-restore</LIcon>
                            </v-btn>
                          </template>
                          <span>{{ $t('workspaceGit.actions.restore') }}</span>
                        </v-tooltip>
                      </div>
                    </transition-group>
                  </template>
                </div>
              </div>
            </div>

            <!-- Commit Card -->
            <div class="git-card" :class="{ 'mt-4': entityMode === 'workspace' }">
              <div class="card-header">
                <LIcon size="18" class="mr-2">mdi-pencil-plus</LIcon>
                {{ $t('workspaceGit.commit.createTitle') }}
              </div>
              <div class="card-content">
                <!-- Summary (Single Mode) -->
                <template v-if="entityMode === 'single'">
                  <div v-if="displayHasChanges" class="commit-summary">
                    <div class="summary-item">
                      <LIcon size="16" color="success">mdi-plus</LIcon>
                      <span>{{ $t('workspaceGit.commit.linesAdded', { count: displayInsertions }) }}</span>
                    </div>
                    <div class="summary-item">
                      <LIcon size="16" color="error">mdi-minus</LIcon>
                      <span>{{ $t('workspaceGit.commit.linesRemoved', { count: displayDeletions }) }}</span>
                    </div>
                    <!-- User changes -->
                    <div v-if="summary?.users?.length > 0" class="user-changes mt-2">
                      <div
                        v-for="u in summary.users"
                        :key="u.username"
                        class="user-change-item"
                      >
                        <span class="user-dot" :style="{ backgroundColor: u.color }" />
                        <span class="user-name">{{ u.username }}</span>
                        <span class="user-lines">{{ $t('workspaceGit.commit.lines', { count: u.changedLines }) }}</span>
                      </div>
                    </div>
                  </div>
                  <div v-else class="no-selection">
                    <LIcon size="28" color="grey-lighten-1" class="mb-2">mdi-check-circle</LIcon>
                    <span>{{ $t('workspaceGit.files.empty') }}</span>
                  </div>
                </template>
                <!-- Summary (Workspace Mode) -->
                <template v-else>
                  <div v-if="selectedFiles.length > 0" class="commit-summary">
                    <div class="summary-item">
                      <LIcon size="16" color="primary">mdi-file-check</LIcon>
                      <span>{{ $t('workspaceGit.commit.selectedFiles', { count: selectedFiles.length }) }}</span>
                    </div>
                    <div class="summary-item">
                      <LIcon size="16" color="success">mdi-plus</LIcon>
                      <span>{{ $t('workspaceGit.commit.linesAdded', { count: totalInsertions }) }}</span>
                    </div>
                    <div class="summary-item">
                      <LIcon size="16" color="error">mdi-minus</LIcon>
                      <span>{{ $t('workspaceGit.commit.linesRemoved', { count: totalDeletions }) }}</span>
                    </div>
                  </div>
                  <div v-else class="no-selection">
                    <LIcon size="28" color="grey-lighten-1" class="mb-2">mdi-checkbox-blank-off-outline</LIcon>
                    <span>{{ $t('workspaceGit.commit.noneSelected') }}</span>
                  </div>
                </template>

                <v-divider class="my-3" />

                <v-alert v-if="commitError" type="error" variant="tonal" class="mb-3" density="compact">
                  {{ commitError }}
                </v-alert>

                <v-textarea
                  v-model="commitMessage"
                  :placeholder="$t('workspaceGit.commit.fullscreenPlaceholder')"
                  variant="outlined"
                  density="compact"
                  :disabled="!canCommit"
                  rows="2"
                  hide-details
                  class="commit-textarea"
                />

                <LBtn
                  variant="primary"
                  :loading="committing"
                  :disabled="!canSubmitCommit"
                  prepend-icon="mdi-check"
                  block
                  class="mt-3"
                  :title="$t('workspaceGit.commit.submitTitle')"
                  @click="handleSubmitCommit"
                >
                  <template v-if="entityMode === 'single'">
                    {{ $t('workspaceGit.commit.submit') }}
                  </template>
                  <template v-else>
                    {{ $t('workspaceGit.commit.submitCount', { count: selectedFiles.length }) }}
                  </template>
                </LBtn>
              </div>
            </div>
          </div>

          <!-- Middle Column: Commit History -->
          <div class="grid-middle">
            <div class="git-card">
              <div class="card-header">
                <LIcon size="18" class="mr-2">mdi-history</LIcon>
                {{ $t('workspaceGit.history.title') }}
                <v-spacer />
                <span class="commit-count">{{ $t('workspaceGit.history.count', { count: recentCommits.length }) }}</span>
              </div>
              <div class="card-content history-content">
                <v-skeleton-loader v-if="loadingCommits" type="list-item@6" />
                <div v-else-if="recentCommits.length === 0" class="empty-state">
                  <LIcon size="36" color="grey-lighten-1" class="mb-2">mdi-source-commit</LIcon>
                  <span>{{ $t('workspaceGit.history.empty') }}</span>
                </div>
                <div v-else class="history-list">
                  <div
                    v-for="c in recentCommits"
                    :key="c.id"
                    class="history-item"
                    :class="{ active: c.id === compareCommitId }"
                    @click="selectCommitForDiff(c.id)"
                  >
                    <div class="commit-indicator" />
                    <div class="commit-details">
                      <div class="commit-message">{{ c.message }}</div>
                      <div class="commit-meta">
                        <span class="author">{{ c.author_username }}</span>
                        <span class="date">{{ formatDate(c.created_at) }}</span>
                        <span class="files-count">{{ $t('workspaceGit.history.files', { count: c.file_count || 1 }) }}</span>
                      </div>
                    </div>
                    <LTag variant="gray" size="sm">#{{ c.id }}</LTag>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Right Column: Diff Viewer -->
          <div class="grid-right">
            <div class="git-card">
              <div class="card-header">
                <LIcon size="18" class="mr-2">mdi-file-compare</LIcon>
                {{ $t('workspaceGit.diff.title') }}
                <v-spacer />
                <v-btn-toggle
                  v-model="compareMode"
                  density="compact"
                  variant="outlined"
                  divided
                  mandatory
                  class="mode-toggle"
                >
                  <v-btn value="working" size="x-small" :title="$t('workspaceGit.diff.workingTitle')">
                    {{ $t('workspaceGit.diff.working') }}
                  </v-btn>
                  <v-btn value="commit-range" size="x-small" :title="$t('workspaceGit.diff.commitTitle')">
                    {{ $t('workspaceGit.diff.commits') }}
                  </v-btn>
                </v-btn-toggle>
              </div>
              <div class="card-content diff-content">
                <!-- No document selected (Workspace Mode Only) -->
                <div v-if="entityMode === 'workspace' && !selectedDocumentId" class="no-document">
                  <LIcon size="40" color="grey-lighten-1" class="mb-2">mdi-file-document-outline</LIcon>
                  <span>{{ $t('workspaceGit.diff.selectFile') }}</span>
                </div>
                <template v-else>
                  <!-- Commit range selectors -->
                  <div v-if="compareMode === 'commit-range'" class="diff-selectors">
                    <v-select
                      v-model="baseCommitId"
                      :items="baseCommitOptions"
                      :label="$t('workspaceGit.diff.baseLabel')"
                      density="compact"
                      variant="outlined"
                      hide-details
                    />
                    <LIcon class="mx-2">mdi-arrow-right</LIcon>
                    <v-select
                      v-model="compareCommitId"
                      :items="commitOptions"
                      :label="$t('workspaceGit.diff.compareLabel')"
                      density="compact"
                      variant="outlined"
                      hide-details
                    />
                  </div>

                  <v-alert v-if="diffError" type="error" variant="tonal" class="mb-3" density="compact">
                    {{ diffError }}
                  </v-alert>

                  <v-skeleton-loader v-if="loadingDiff" type="table" height="300" />
                  <DiffViewer
                    v-else
                    :base-text="diffBaseText"
                    :compare-text="diffCompareText"
                    :base-label="diffBaseLabel"
                    :compare-label="diffCompareLabel"
                    class="diff-viewer"
                  />
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </v-dialog>

  <!-- Rollback Confirmation Dialog -->
  <v-dialog v-model="showRollbackConfirm" max-width="420" persistent>
    <v-card class="rollback-card">
      <v-card-title class="d-flex align-center ga-2">
        <LIcon color="warning">mdi-alert-circle</LIcon>
        {{ $t('workspaceGit.rollback.title') }}
      </v-card-title>
      <v-card-text>
        <p v-if="forceRollback">
          <i18n-t keypath="workspaceGit.rollback.forceConfirm" tag="span">
            <template #path>
              <strong>{{ rollbackTarget?.path }}</strong>
            </template>
          </i18n-t>
        </p>
        <p v-else>
          <i18n-t keypath="workspaceGit.rollback.confirm" tag="span">
            <template #path>
              <strong>{{ rollbackTarget?.path }}</strong>
            </template>
          </i18n-t>
        </p>
        <p class="text-medium-emphasis mt-2 mb-0">
          {{ $t('workspaceGit.rollback.resetHint') }}
          <span v-if="forceRollbackDetails?.commit_id">
            {{ $t('workspaceGit.rollback.commitHint', { id: forceRollbackDetails.commit_id }) }}
          </span>
        </p>
      </v-card-text>
      <v-card-actions class="pa-4 pt-0">
        <v-spacer />
        <LBtn variant="cancel" @click="cancelRollback">
          {{ $t('common.cancel') }}
        </LBtn>
        <LBtn variant="danger" prepend-icon="mdi-undo" @click="handleExecuteRollback">
          {{ $t('workspaceGit.rollback.confirmAction') }}
        </LBtn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch, toRef } from 'vue'
import axios from 'axios'
import { useI18n } from 'vue-i18n'
import { useGitStatus } from '@/composables/useGitStatus'
import DiffViewer from './DiffViewer.vue'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const INITIAL_BASE = '__initial__'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // Generic entity ID (workspace or prompt)
  entityId: { type: Number, default: null },
  // Legacy prop - maps to entityId for backwards compatibility
  workspaceId: { type: Number, default: null },
  // Mode: 'workspace' (multiple documents) or 'single' (single entity like prompts)
  entityMode: { type: String, default: 'workspace' },
  selectedDocumentId: { type: Number, default: null },
  canCommit: { type: Boolean, default: false },
  apiPrefix: { type: String, default: '/api/latex-collab' },
  getContent: { type: Function, default: null },
  beforeRollback: { type: Function, default: null },
  beforeCommit: { type: Function, default: null },
  // For single mode: reactive summary object
  summary: { type: Object, default: () => ({ users: [], totalChangedLines: 0, hasChanges: false, insertions: 0, deletions: 0 }) }
})

const emit = defineEmits(['update:modelValue', 'committed', 'rollback', 'restored'])
const { t, locale } = useI18n()

// Resolve entity ID (entityId takes precedence, falls back to workspaceId)
const resolvedEntityId = computed(() => props.entityId ?? props.workspaceId)
const entityIdRef = toRef(() => resolvedEntityId.value)
const summaryRef = toRef(() => props.summary)

// Use shared git status composable
const {
  changedFiles,
  deletedFiles,
  selectedFiles,
  checkingChanges,
  loadError,
  restoringFile,
  commitMessage,
  committing,
  commitError,
  recentCommits,
  loadingCommits,
  rollingBack,
  showRollbackConfirm,
  rollbackTarget,
  forceRollback,
  forceRollbackDetails,
  changedCount,
  deletedCount,
  totalInsertions,
  totalDeletions,
  canSubmitCommit,
  singleModeHasChanges,
  singleModeInsertions,
  singleModeDeletions,
  formatDate,
  getFileIcon,
  getFileIconColor,
  getStatusBadge,
  toggleFile,
  selectAll,
  deselectAll,
  submitCommit,
  executeRollback,
  confirmRollback,
  cancelRollback,
  restoreFile,
  refresh
} = useGitStatus(entityIdRef, {
  apiPrefix: props.apiPrefix,
  entityMode: props.entityMode,
  summary: summaryRef,
  getContent: props.getContent,
  autoSetup: false // Dialog controls its own lifecycle
})

// Computed for mode-aware display
const displayHasChanges = computed(() => {
  if (props.entityMode === 'single') {
    return props.summary?.hasChanges === true || (props.summary?.totalChangedLines || 0) > 0
  }
  return changedCount.value > 0
})

const displayInsertions = computed(() => {
  if (props.entityMode === 'single') {
    return props.summary?.insertions || 0
  }
  return totalInsertions.value
})

const displayDeletions = computed(() => {
  if (props.entityMode === 'single') {
    return props.summary?.deletions || 0
  }
  return totalDeletions.value
})

// Local diff state
const compareMode = ref('working')
const baseCommitId = ref(INITIAL_BASE)
const compareCommitId = ref(null)
const diffBaseText = ref('')
const diffCompareText = ref('')
const diffBaseLabel = ref('')
const diffCompareLabel = ref('')
const diffError = ref('')
const loadingDiff = ref(false)
const baselineSnapshot = ref('')
const baselineCommitId = ref(null)
const baselineCommitMessage = ref('')
const commitSnapshotCache = new Map()

// Computed
const commitOptions = computed(() => recentCommits.value.map((c) => ({
  title: `#${c.id} · ${c.message}`,
  value: c.id
})))

const baseCommitOptions = computed(() => [
  { title: t('workspaceGit.diff.initial'), value: INITIAL_BASE },
  ...commitOptions.value
])

// Helpers
function authHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function getCommitById(commitId) {
  return recentCommits.value.find((c) => c.id === commitId) || null
}

function formatCommitLabel(commit) {
  if (!commit) return t('workspaceGit.diff.emptyLabel')
  const message = commit.message ? String(commit.message).trim() : ''
  return `#${commit.id}${message ? ` · ${message}` : ''}`
}

// Diff functions
async function loadBaselineSnapshot(force = false) {
  if (props.entityMode === 'single') {
    // Single mode: Load baseline for the entity
    if (!resolvedEntityId.value) return
    if (!force && baselineCommitId.value !== null) return

    const res = await axios.get(
      `${API_BASE}${props.apiPrefix}/${resolvedEntityId.value}/baseline`,
      { headers: authHeaders() }
    )
    baselineSnapshot.value = res.data?.baseline || res.data?.content || ''
    baselineCommitId.value = res.data?.commit_id ?? null
    baselineCommitMessage.value = res.data?.commit_message || ''
  } else {
    // Workspace mode: Load baseline for the selected document
    if (!props.selectedDocumentId) return
    if (!force && baselineCommitId.value !== null) return

    const res = await axios.get(
      `${API_BASE}${props.apiPrefix}/documents/${props.selectedDocumentId}/baseline`,
      { headers: authHeaders() }
    )
    baselineSnapshot.value = res.data?.baseline || ''
    baselineCommitId.value = res.data?.commit_id ?? null
    baselineCommitMessage.value = res.data?.commit_message || ''
  }
}

async function fetchCommitSnapshot(commitId) {
  if (!commitId || commitId === INITIAL_BASE) return ''
  if (commitSnapshotCache.has(commitId)) {
    return commitSnapshotCache.get(commitId) || ''
  }

  let res
  if (props.entityMode === 'single') {
    if (!resolvedEntityId.value) return ''
    res = await axios.get(
      `${API_BASE}${props.apiPrefix}/${resolvedEntityId.value}/commits/${commitId}`,
      { headers: authHeaders() }
    )
  } else {
    if (!props.selectedDocumentId) return ''
    res = await axios.get(
      `${API_BASE}${props.apiPrefix}/documents/${props.selectedDocumentId}/commits/${commitId}`,
      { headers: authHeaders() }
    )
  }

  const snapshot = res.data?.commit?.content_snapshot || ''
  commitSnapshotCache.set(commitId, snapshot)
  return snapshot
}

async function refreshDiff(force = false) {
  // For workspace mode, require a selected document
  if (props.entityMode === 'workspace' && !props.selectedDocumentId) {
    diffBaseText.value = ''
    diffCompareText.value = ''
    diffBaseLabel.value = t('workspaceGit.diff.noDocument')
    diffCompareLabel.value = t('workspaceGit.diff.emptyLabel')
    return
  }

  // For single mode, require entity ID
  if (props.entityMode === 'single' && !resolvedEntityId.value) {
    diffBaseText.value = ''
    diffCompareText.value = ''
    diffBaseLabel.value = t('workspaceGit.diff.emptyLabel')
    diffCompareLabel.value = t('workspaceGit.diff.emptyLabel')
    return
  }

  loadingDiff.value = true
  diffError.value = ''

  try {
    if (compareMode.value === 'working') {
      await loadBaselineSnapshot(force)
      diffBaseText.value = baselineSnapshot.value || ''
      diffCompareText.value = props.getContent ? String(props.getContent() || '') : ''
      diffBaseLabel.value = baselineCommitId.value
        ? `#${baselineCommitId.value}${baselineCommitMessage.value ? ` · ${baselineCommitMessage.value}` : ''}`
        : t('workspaceGit.diff.initial')
      diffCompareLabel.value = t('workspaceGit.diff.workingTree')
      return
    }

    const compareCommit = getCommitById(compareCommitId.value)
    if (!compareCommit) {
      diffBaseText.value = ''
      diffCompareText.value = ''
      diffBaseLabel.value = t('workspaceGit.diff.emptyLabel')
      diffCompareLabel.value = t('workspaceGit.diff.emptyLabel')
      return
    }

    const baseCommit = getCommitById(baseCommitId.value)
    const [compareSnapshot, baseSnapshot] = await Promise.all([
      fetchCommitSnapshot(compareCommit.id),
      fetchCommitSnapshot(baseCommit?.id || baseCommitId.value)
    ])

    diffBaseText.value = baseSnapshot || ''
    diffCompareText.value = compareSnapshot || ''
    diffBaseLabel.value = baseCommit
      ? formatCommitLabel(baseCommit)
      : t('workspaceGit.diff.initial')
    diffCompareLabel.value = formatCommitLabel(compareCommit)
  } catch (e) {
    diffBaseText.value = ''
    diffCompareText.value = ''
    diffBaseLabel.value = t('workspaceGit.diff.emptyLabel')
    diffCompareLabel.value = t('workspaceGit.diff.emptyLabel')
    diffError.value = e?.response?.data?.error || e?.message || t('workspaceGit.errors.diffFailed')
  } finally {
    loadingDiff.value = false
  }
}

function selectCommitForDiff(commitId) {
  if (!commitId) return
  compareCommitId.value = commitId
  compareMode.value = 'commit-range'
  if (!baseCommitId.value || baseCommitId.value === commitId) {
    const selectedIndex = recentCommits.value.findIndex((c) => c.id === commitId)
    const previous = selectedIndex >= 0 ? recentCommits.value[selectedIndex + 1] : null
    baseCommitId.value = previous ? previous.id : INITIAL_BASE
  }
}

function resetDiffState() {
  diffBaseText.value = ''
  diffCompareText.value = ''
  diffBaseLabel.value = ''
  diffCompareLabel.value = ''
  diffError.value = ''
  compareMode.value = 'working'
  baseCommitId.value = INITIAL_BASE
  compareCommitId.value = null
  baselineSnapshot.value = ''
  baselineCommitId.value = null
  baselineCommitMessage.value = ''
  commitSnapshotCache.clear()
}

// Event handlers
async function handleSubmitCommit() {
  const success = await submitCommit({ beforeCommit: props.beforeCommit })
  if (success) {
    emit('committed')
  }
}

async function handleExecuteRollback() {
  const result = await executeRollback({ beforeRollback: props.beforeRollback })
  if (result && result.documentId) {
    emit('rollback', result)
  }
}

async function handleRestoreFile(file) {
  const restoredId = await restoreFile(file)
  if (restoredId) {
    emit('restored', restoredId)
  }
}

// Watchers
watch(() => props.modelValue, async (isOpen) => {
  if (isOpen) {
    await refresh()
    // For single mode, always refresh diff; for workspace mode, only if document selected
    if (props.entityMode === 'single' || props.selectedDocumentId) {
      await refreshDiff(true)
    }
  } else {
    resetDiffState()
  }
})

// Only watch selectedDocumentId in workspace mode
watch(() => props.selectedDocumentId, async (newId, oldId) => {
  if (props.entityMode === 'workspace' && newId !== oldId && props.modelValue) {
    resetDiffState()
    if (newId) {
      await refreshDiff(true)
    }
  }
})

watch(compareMode, async () => {
  if (props.modelValue) {
    await refreshDiff(false)
  }
})

watch([baseCommitId, compareCommitId], async () => {
  if (compareMode.value === 'commit-range' && props.modelValue) {
    await refreshDiff(false)
  }
})
</script>

<style scoped>
/* LLARS Design Variables */
.git-detail-dialog {
  --llars-primary: #b0ca97;
  --llars-secondary: #D1BC8A;
  --llars-accent: #88c4c8;
  --llars-success: #98d4bb;
  --llars-warning: #e8c87a;
  --llars-danger: #e8a087;
  --llars-gray: #9e9e9e;
  --llars-radius: 16px 4px 16px 4px;
  --llars-radius-sm: 8px 2px 8px 2px;

  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius);
  overflow: hidden;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}

/* Header */
.dialog-header {
  background: linear-gradient(135deg, var(--llars-primary) 0%, var(--llars-accent) 100%);
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.header-icon-box {
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 8px 2px 8px 2px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-title {
  font-weight: 600;
  font-size: 16px;
  color: white;
}

/* Content */
.dialog-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.content-grid {
  display: grid;
  grid-template-columns: 280px 280px 1fr;
  gap: 16px;
  min-height: 450px;
}

/* Single mode: Narrower first column (just commit, no file selection) */
.content-grid.single-mode {
  grid-template-columns: 250px 280px 1fr;
}

/* Git Card */
.git-card {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: var(--llars-radius-sm);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.card-header {
  padding: 10px 14px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  font-weight: 600;
  font-size: 13px;
  display: flex;
  align-items: center;
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.card-content {
  padding: 12px;
  flex: 1;
  overflow-y: auto;
}

/* File Count */
.file-count, .commit-count {
  font-weight: 400;
  font-size: 11px;
  color: rgb(var(--v-theme-on-surface-variant));
}

/* Bulk Actions */
.bulk-actions {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
  margin-bottom: 8px;
}

/* File List */
.file-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s;
}

.file-item:hover {
  background: rgba(var(--v-theme-primary), 0.05);
}

.file-item.selected {
  background: rgba(var(--v-theme-primary), 0.12);
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-path {
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.file-stats {
  display: flex;
  gap: 6px;
}

.stat-badge {
  font-size: 10px;
  font-family: monospace;
  padding: 1px 5px;
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
  width: 18px;
  height: 18px;
  font-size: 10px;
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

/* Deleted Files */
.deleted-section-title {
  font-size: 11px;
  font-weight: 600;
  color: rgb(var(--v-theme-error));
  display: flex;
  align-items: center;
  padding: 6px 0;
  margin-bottom: 4px;
}

.deleted-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.deleted-item {
  display: flex;
  align-items: center;
  padding: 6px 10px;
  background: rgba(232, 160, 135, 0.08);
  border-radius: 4px;
}

.deleted-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.deleted-name {
  font-size: 12px;
  font-weight: 500;
  text-decoration: line-through;
  color: rgb(var(--v-theme-error));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.deleted-date {
  font-size: 10px;
  color: rgb(var(--v-theme-on-surface-variant));
}

/* Commit Summary */
.commit-summary {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

/* User Changes (Single Mode) */
.user-changes {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  padding-top: 8px;
}

.user-change-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 12px;
}

.user-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.user-name {
  flex: 1;
  font-weight: 500;
}

.user-lines {
  color: rgb(var(--v-theme-on-surface-variant));
  font-size: 11px;
}

.no-selection {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  color: rgb(var(--v-theme-on-surface-variant));
  font-size: 12px;
}

.commit-textarea :deep(.v-field) {
  border-radius: var(--llars-radius-sm) !important;
}

/* History */
.history-content {
  padding: 6px !important;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s;
}

.history-item:hover {
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.history-item.active {
  background: rgba(var(--v-theme-primary), 0.12);
}

.history-item.active .commit-indicator {
  background: var(--llars-accent);
  box-shadow: 0 0 0 2px rgba(136, 196, 200, 0.3);
}

.commit-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--llars-primary);
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
  margin-bottom: 2px;
}

.commit-meta {
  font-size: 10px;
  color: rgb(var(--v-theme-on-surface-variant));
  display: flex;
  gap: 6px;
}

/* Diff Section */
.diff-content {
  display: flex;
  flex-direction: column;
}

.diff-selectors {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
}

.diff-selectors .v-select {
  flex: 1;
}

.no-document {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 16px;
  color: rgb(var(--v-theme-on-surface-variant));
  font-size: 12px;
  text-align: center;
}

.diff-viewer {
  flex: 1;
  min-height: 0;
}

.mode-toggle {
  border-radius: var(--llars-radius-sm) !important;
}

.mode-toggle .v-btn {
  font-size: 10px !important;
  text-transform: none !important;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: rgb(var(--v-theme-on-surface-variant));
  font-size: 12px;
}

/* Rollback Card */
.rollback-card {
  border-radius: var(--llars-radius) !important;
}

.rollback-card .v-card-title {
  font-size: 15px;
  font-weight: 600;
  padding-bottom: 8px;
}

/* Grid columns */
.grid-left,
.grid-middle,
.grid-right {
  display: flex;
  flex-direction: column;
}

/* File List Transitions */
.file-list-enter-active,
.file-list-leave-active {
  transition: all 0.2s ease;
}

.file-list-enter-from {
  opacity: 0;
  transform: translateX(-8px);
}

.file-list-leave-to {
  opacity: 0;
  transform: translateX(8px);
}

.file-list-move {
  transition: transform 0.2s ease;
}

/* Responsive */
@media (max-width: 1000px) {
  .content-grid {
    grid-template-columns: 1fr 1fr;
  }

  .grid-right {
    grid-column: span 2;
  }
}

@media (max-width: 700px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .grid-right {
    grid-column: span 1;
  }
}
</style>
