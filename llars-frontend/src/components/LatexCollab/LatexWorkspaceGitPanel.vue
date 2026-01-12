<template>
  <div class="git-panel-wrapper">
    <!-- Collapsed State: Thin bar -->
    <div v-if="!expanded && !fullscreen" class="git-panel-collapsed" @click="expanded = true">
      <div class="collapsed-content">
        <div class="collapsed-icon-box">
          <LIcon size="18">mdi-source-branch</LIcon>
        </div>
        <span class="collapsed-label">{{ $t('workspaceGit.title') }}</span>
        <LTag
          v-if="changedFiles.length > 0"
          variant="warning"
          size="small"
        >
          {{ changedFiles.length }} {{ changedFiles.length === 1 ? $t('workspaceGit.fileSingular') : $t('workspaceGit.filePlural') }}
        </LTag>
        <LTag
          v-if="deletedFiles.length > 0"
          variant="danger"
          size="small"
        >
          {{ $t('workspaceGit.tags.deleted', { count: deletedFiles.length }) }}
        </LTag>
        <LTag v-if="changedFiles.length === 0 && deletedFiles.length === 0" variant="gray" size="small">
          {{ $t('workspaceGit.tags.noChanges') }}
        </LTag>
        <v-spacer />
        <LIcon size="18" class="expand-icon">mdi-chevron-up</LIcon>
      </div>
    </div>

    <!-- Expanded State: Panel -->
    <div v-if="expanded && !fullscreen" class="git-panel-expanded">
      <!-- Header -->
      <div class="panel-header">
        <div class="header-icon-box">
          <LIcon size="20" color="white">mdi-source-branch</LIcon>
        </div>
        <span class="header-title">{{ $t('workspaceGit.header.title') }}</span>
        <LTag
          v-if="changedFiles.length > 0"
          variant="warning"
          size="small"
        >
          {{ $t('workspaceGit.tags.changed', { count: changedFiles.length }) }}
        </LTag>
        <LTag
          v-if="deletedFiles.length > 0"
          variant="danger"
          size="small"
        >
          {{ $t('workspaceGit.tags.deleted', { count: deletedFiles.length }) }}
        </LTag>
        <LTag v-if="changedFiles.length === 0 && deletedFiles.length === 0" variant="success" size="small">
          {{ $t('workspaceGit.tags.synced') }}
        </LTag>
        <v-spacer />
        <div class="header-actions">
          <v-btn
            icon
            variant="text"
            size="small"
            :title="$t('workspaceGit.actions.refresh')"
            :loading="checkingChanges"
            @click="checkForChanges"
          >
            <LIcon size="18">mdi-refresh</LIcon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            :title="$t('workspaceGit.actions.fullscreen')"
            @click="fullscreen = true"
          >
            <LIcon size="18">mdi-fullscreen</LIcon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            :title="$t('workspaceGit.actions.collapse')"
            @click="expanded = false"
          >
            <LIcon size="18">mdi-chevron-down</LIcon>
          </v-btn>
        </div>
      </div>

      <!-- Content -->
      <div class="panel-content">
        <v-alert v-if="loadError" type="error" variant="tonal" class="mb-3" density="compact">
          {{ loadError }}
        </v-alert>

        <!-- Two columns: Files + Commit -->
        <div class="content-grid">
          <!-- Left: Changed Files -->
          <div class="files-section">
            <div class="section-title">
              <LIcon size="16" class="mr-1">mdi-file-document-multiple</LIcon>
              {{ $t('workspaceGit.files.title') }}
              <v-spacer />
              <span v-if="changedFiles.length > 0" class="file-count">
                {{ selectedFiles.length }}/{{ changedFiles.length }}
              </span>
            </div>

            <v-skeleton-loader v-if="checkingChanges" type="list-item@3" />
            <div v-else-if="changedFiles.length === 0 && deletedFiles.length === 0" class="empty-files">
              {{ $t('workspaceGit.files.empty') }}
            </div>
            <div v-else class="file-list">
              <!-- Select All (only if there are changed files) -->
              <div v-if="changedFiles.length > 0" class="select-all-row">
                <v-checkbox
                  v-model="allSelected"
                  density="compact"
                  hide-details
                  :indeterminate="someSelected && !allSelected"
                  @update:model-value="toggleSelectAll"
                >
                  <template #label>
                    <span class="select-all-label">{{ $t('workspaceGit.files.selectAll') }}</span>
                  </template>
                </v-checkbox>
              </div>

              <!-- Changed File list -->
              <div
                v-for="file in changedFiles"
                :key="file.id"
                class="file-item"
                :class="{ selected: selectedFiles.includes(file.id) }"
              >
                <v-checkbox
                  :model-value="selectedFiles.includes(file.id)"
                  density="compact"
                  hide-details
                  @update:model-value="toggleFile(file.id)"
                />
                <!-- Status badge -->
                <v-tooltip location="top">
                  <template #activator="{ props: tp }">
                    <span v-bind="tp" class="status-badge" :class="getStatusBadge(file).color">
                      {{ getStatusBadge(file).text }}
                    </span>
                  </template>
                  <span>{{ getStatusBadge(file).tooltip }}</span>
                </v-tooltip>
                <LIcon size="16" class="file-icon">mdi-file-document-outline</LIcon>
                <div class="file-info">
                  <span class="file-path">{{ file.path }}</span>
                  <span class="file-stats">
                    <span class="text-success">+{{ file.insertions }}</span>
                    <span class="mx-1">/</span>
                    <span class="text-error">-{{ file.deletions }}</span>
                  </span>
                </div>
                <!-- Rollback button -->
                <v-tooltip v-if="file.has_baseline" location="top">
                  <template #activator="{ props: tp }">
                    <v-btn
                      v-bind="tp"
                      icon
                      variant="text"
                      size="x-small"
                      color="warning"
                      :loading="rollingBack === file.id"
                      @click.stop="confirmRollback(file)"
                    >
                      <LIcon size="14">mdi-undo</LIcon>
                    </v-btn>
                  </template>
                  <span>{{ $t('workspaceGit.actions.discard') }}</span>
                </v-tooltip>
              </div>

              <!-- Deleted Files Section -->
              <template v-if="deletedFiles.length > 0">
                <v-divider v-if="changedFiles.length > 0" class="my-2" />
                <div class="deleted-section-title">
                  <LIcon size="14" color="error" class="mr-1">mdi-delete</LIcon>
                  {{ $t('workspaceGit.files.deletedTitle') }}
                </div>
                <div
                  v-for="file in deletedFiles"
                  :key="'deleted-' + file.id"
                  class="file-item deleted"
                >
                  <!-- Status badge -->
                  <span class="status-badge error">D</span>
                  <LIcon size="16" class="file-icon" color="error">mdi-file-remove-outline</LIcon>
                  <div class="file-info">
                    <span class="file-path deleted-path">{{ file.title }}</span>
                  </div>
                  <!-- Restore button -->
                  <v-tooltip location="top">
                    <template #activator="{ props: tp }">
                      <v-btn
                        v-bind="tp"
                        icon
                        variant="text"
                        size="x-small"
                        color="success"
                        :loading="restoringFile === file.id"
                        @click.stop="restoreFile({ id: file.id, ...file })"
                      >
                        <LIcon size="14">mdi-restore</LIcon>
                      </v-btn>
                    </template>
                    <span>{{ $t('workspaceGit.actions.restore') }}</span>
                  </v-tooltip>
                </div>
              </template>
            </div>
          </div>

          <!-- Right: Commit Section -->
          <div class="commit-section">
            <div class="section-title">
              <LIcon size="16" class="mr-1">mdi-pencil-plus</LIcon>
              {{ $t('workspaceGit.commit.title') }}
            </div>

            <v-alert v-if="commitError" type="error" variant="tonal" class="mb-2" density="compact">
              {{ commitError }}
            </v-alert>

            <v-text-field
              v-model="commitMessage"
              :placeholder="$t('workspaceGit.commit.placeholder')"
              variant="outlined"
              density="compact"
              :disabled="!canCommit"
              hide-details
              class="commit-input"
            />

            <div class="commit-actions">
              <LBtn
                variant="primary"
                size="small"
                :loading="committing"
                :disabled="!canSubmitCommit"
                prepend-icon="mdi-check"
                :title="$t('workspaceGit.commit.submitTitle')"
                @click="submitCommit"
              >
                {{ $t('workspaceGit.commit.submitLabel', { count: selectedFiles.length }) }}
              </LBtn>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Fullscreen Dialog -->
    <v-dialog v-model="fullscreen" fullscreen transition="dialog-bottom-transition">
      <div class="git-fullscreen">
        <!-- Fullscreen Header -->
        <div class="fullscreen-header">
          <div class="header-icon-box large">
            <LIcon size="24" color="white">mdi-source-branch</LIcon>
          </div>
          <span class="header-title">{{ $t('workspaceGit.fullscreen.title') }}</span>
          <LTag
            v-if="changedFiles.length > 0"
            variant="warning"
            size="small"
          >
            {{ $t('workspaceGit.fullscreen.changedCount', { count: changedFiles.length }) }}
          </LTag>
          <LTag
            v-if="deletedFiles.length > 0"
            variant="danger"
            size="small"
          >
            {{ $t('workspaceGit.tags.deleted', { count: deletedFiles.length }) }}
          </LTag>
          <v-spacer />
          <LBtn
            variant="text"
            size="small"
            prepend-icon="mdi-refresh"
            :loading="checkingChanges"
            :title="$t('workspaceGit.actions.refresh')"
            @click="checkForChanges"
          >
            {{ $t('common.refresh') }}
          </LBtn>
          <LBtn
            variant="cancel"
            size="small"
            prepend-icon="mdi-fullscreen-exit"
            class="ml-2"
            :title="$t('workspaceGit.actions.exitFullscreen')"
            @click="fullscreen = false"
          >
            {{ $t('common.close') }}
          </LBtn>
        </div>

        <!-- Fullscreen Content -->
        <div class="fullscreen-content">
          <v-alert v-if="loadError" type="error" variant="tonal" class="mb-4">
            {{ loadError }}
          </v-alert>

          <div class="fullscreen-grid">
            <!-- Left Column: Changed Files + Commit -->
            <div class="fullscreen-left">
              <!-- Changed Files Card -->
              <div class="git-card">
                <div class="card-header">
                  <LIcon size="18" class="mr-2">mdi-file-document-multiple</LIcon>
                  {{ $t('workspaceGit.files.title') }}
                  <v-spacer />
                  <span class="file-count-header">{{ selectedFiles.length }}/{{ changedFiles.length }}</span>
                </div>
                <div class="card-content">
                  <v-skeleton-loader v-if="checkingChanges" type="list-item@6" />
                  <div v-else-if="changedFiles.length === 0 && deletedFiles.length === 0" class="empty-state">
                    <LIcon size="48" color="grey-lighten-1" class="mb-2">mdi-check-circle</LIcon>
                    <span>{{ $t('workspaceGit.files.emptyUncommitted') }}</span>
                  </div>
                  <div v-else>
                    <!-- Select All / None buttons (only if there are changed files) -->
                    <div v-if="changedFiles.length > 0" class="bulk-actions">
                      <LBtn variant="text" size="small" @click="selectAll">
                        {{ $t('workspaceGit.files.selectAll') }}
                      </LBtn>
                      <LBtn variant="text" size="small" @click="deselectAll">
                        {{ $t('workspaceGit.files.selectNone') }}
                      </LBtn>
                    </div>

                    <v-divider v-if="changedFiles.length > 0" class="my-2" />

                    <!-- Changed File list -->
                    <div class="file-list-full">
                      <div
                        v-for="file in changedFiles"
                        :key="file.id"
                        class="file-item-full"
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
                        <!-- Status badge -->
                        <v-tooltip location="top">
                          <template #activator="{ props: tp }">
                            <span v-bind="tp" class="status-badge-full" :class="getStatusBadge(file).color">
                              {{ getStatusBadge(file).text }}
                            </span>
                          </template>
                          <span>{{ getStatusBadge(file).tooltip }}</span>
                        </v-tooltip>
                        <LIcon size="20" class="file-icon" :color="getFileIconColor(file.path)">
                          {{ getFileIcon(file.path) }}
                        </LIcon>
                        <div class="file-details">
                          <div class="file-path-full">{{ file.path }}</div>
                          <div class="file-stats-full">
                            <span class="stat-badge success">+{{ file.insertions }}</span>
                            <span class="stat-badge error">-{{ file.deletions }}</span>
                          </div>
                        </div>
                        <!-- Rollback button -->
                        <v-tooltip v-if="file.has_baseline" location="left">
                          <template #activator="{ props: tp }">
                            <v-btn
                              v-bind="tp"
                              icon
                              variant="tonal"
                              size="small"
                              color="warning"
                              :loading="rollingBack === file.id"
                              @click.stop="confirmRollback(file)"
                            >
                              <LIcon size="18">mdi-undo</LIcon>
                            </v-btn>
                          </template>
                          <span>{{ $t('workspaceGit.actions.discard') }}</span>
                        </v-tooltip>
                      </div>

                    </div>
                  </div>
                </div>
              </div>

              <!-- Deleted Files Card -->
              <div v-if="deletedFiles.length > 0" class="git-card mt-4">
                <div class="card-header deleted-header">
                  <LIcon size="18" class="mr-2" color="error">mdi-delete</LIcon>
                  {{ $t('workspaceGit.files.deletedTitle') }}
                  <v-spacer />
                  <span class="deleted-count">{{ deletedFiles.length }}</span>
                </div>
                <div class="card-content">
                  <div class="deleted-files-list">
                    <div
                      v-for="file in deletedFiles"
                      :key="'deleted-' + file.id"
                      class="deleted-file-item"
                    >
                      <span class="status-badge error">D</span>
                      <LIcon size="16" color="error" class="mr-2">mdi-file-remove-outline</LIcon>
                      <div class="deleted-file-info">
                        <span class="deleted-file-name">{{ file.title }}</span>
                        <span class="deleted-file-date">{{ formatDate(file.deleted_at) }}</span>
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
                            @click.stop="restoreFile({ id: file.id, ...file })"
                          >
                            <LIcon size="14">mdi-restore</LIcon>
                          </v-btn>
                        </template>
                        <span>{{ $t('workspaceGit.actions.restore') }}</span>
                      </v-tooltip>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Commit Card -->
              <div class="git-card mt-4">
                <div class="card-header">
                  <LIcon size="18" class="mr-2">mdi-pencil-plus</LIcon>
                  {{ $t('workspaceGit.commit.createTitle') }}
                </div>
                <div class="card-content">
                  <!-- Summary -->
                  <div v-if="selectedFiles.length > 0" class="commit-summary">
                    <div class="summary-item">
                      <LIcon size="16" color="primary">mdi-file-check</LIcon>
                      <span>
                        {{ $t('workspaceGit.commit.selectedFiles', { count: selectedFiles.length }) }}
                      </span>
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
                    <LIcon size="32" color="grey-lighten-1" class="mb-2">mdi-checkbox-blank-off-outline</LIcon>
                    <span>{{ $t('workspaceGit.commit.noneSelected') }}</span>
                  </div>

                  <v-divider class="my-4" />

                  <v-alert v-if="commitError" type="error" variant="tonal" class="mb-3">
                    {{ commitError }}
                  </v-alert>

                  <v-textarea
                    v-model="commitMessage"
                    :placeholder="$t('workspaceGit.commit.fullscreenPlaceholder')"
                    variant="outlined"
                    density="comfortable"
                    :disabled="!canCommit"
                    rows="3"
                    hide-details
                    class="commit-textarea"
                  />

                  <div class="commit-actions-full mt-4">
                    <LBtn
                      variant="primary"
                      :loading="committing"
                      :disabled="!canSubmitCommit"
                      prepend-icon="mdi-check"
                      block
                      :title="$t('workspaceGit.commit.submitTitle')"
                      @click="submitCommit"
                    >
                      {{ $t('workspaceGit.commit.submitCount', { count: selectedFiles.length }) }}
                    </LBtn>
                  </div>
                </div>
              </div>
            </div>

            <!-- Middle Column: Commit History -->
            <div class="fullscreen-middle">
              <div class="git-card">
                <div class="card-header">
                  <LIcon size="18" class="mr-2">mdi-history</LIcon>
                  {{ $t('workspaceGit.history.title') }}
                  <v-spacer />
                  <span class="commit-count">{{ $t('workspaceGit.history.count', { count: recentCommits.length }) }}</span>
                </div>
                <div class="card-content history-content">
                  <v-skeleton-loader v-if="loadingCommits" type="list-item@8" />
                  <div v-else-if="recentCommits.length === 0" class="empty-state">
                    <LIcon size="48" color="grey-lighten-1" class="mb-2">mdi-source-commit</LIcon>
                    <span>{{ $t('workspaceGit.history.empty') }}</span>
                  </div>
                  <div v-else class="history-list-full">
                    <div
                      v-for="c in recentCommits"
                      :key="c.id"
                      class="history-item-full"
                      :class="{ active: c.id === compareCommitId }"
                      @click="selectCommitForDiff(c.id)"
                    >
                      <div class="commit-indicator" />
                      <div class="commit-details">
                        <div class="commit-message-full">{{ c.message }}</div>
                        <div class="commit-meta-full">
                          <span class="author">{{ c.author_username }}</span>
                          <span class="date">{{ formatDate(c.created_at) }}</span>
                          <span class="files-count">{{ $t('workspaceGit.history.files', { count: c.file_count || 1 }) }}</span>
                        </div>
                      </div>
                      <LTag variant="gray" size="small">#{{ c.id }}</LTag>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Right Column: Diff Viewer -->
            <div class="fullscreen-right">
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
                    <v-btn value="working" size="small" :title="$t('workspaceGit.diff.workingTitle')">{{ $t('workspaceGit.diff.working') }}</v-btn>
                    <v-btn value="commit-range" size="small" :title="$t('workspaceGit.diff.commitTitle')">{{ $t('workspaceGit.diff.commits') }}</v-btn>
                  </v-btn-toggle>
                </div>
                <div class="card-content diff-content">
                  <!-- No document selected message -->
                  <div v-if="!selectedDocumentId" class="no-document-selected">
                    <LIcon size="48" color="grey-lighten-1" class="mb-2">mdi-file-document-outline</LIcon>
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

                    <v-alert v-if="diffError" type="error" variant="tonal" class="mb-3">
                      {{ diffError }}
                    </v-alert>

                    <v-skeleton-loader v-if="isLoading('diff')" type="table" height="400" />
                    <MarkdownDiffViewer
                      v-else
                      :base-text="diffBaseText"
                      :compare-text="diffCompareText"
                      :base-label="diffBaseLabel"
                      :compare-label="diffCompareLabel"
                      class="diff-viewer-full"
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
      <v-card class="rollback-confirm-card">
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
          <LBtn variant="danger" prepend-icon="mdi-undo" @click="executeRollback">
            {{ $t('workspaceGit.rollback.confirmAction') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import axios from 'axios'
import { useI18n } from 'vue-i18n'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import MarkdownDiffViewer from '@/components/MarkdownCollab/MarkdownDiffViewer.vue'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'
import { getSocket } from '@/services/socketService'

const props = defineProps({
  workspaceId: { type: Number, required: true },
  canCommit: { type: Boolean, default: false },
  apiPrefix: { type: String, default: '/api/latex-collab' },
  // For diff viewer: provide the selected document ID and content getter
  selectedDocumentId: { type: Number, default: null },
  getContent: { type: Function, default: null },
  beforeRollback: { type: Function, default: null },
  beforeCommit: { type: Function, default: null }
})

const emit = defineEmits(['committed', 'rollback', 'restored'])
const { t, locale } = useI18n()

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080'
const { isLoading, withLoading } = useSkeletonLoading(['commits', 'diff'])

const expanded = ref(false)
const fullscreen = ref(false)

// Changed files state
const changedFiles = ref([])
const deletedFiles = ref([])
const selectedFiles = ref([])
const checkingChanges = ref(false)
const loadError = ref('')
const restoringFile = ref(null) // file id being restored

// Commit state
const commitMessage = ref('')
const committing = ref(false)
const commitError = ref('')

// Recent commits
const recentCommits = ref([])
const loadingCommits = ref(false)

// Rollback state
const rollingBack = ref(null) // file id being rolled back
const showRollbackConfirm = ref(false)
const rollbackTarget = ref(null) // file to rollback
const forceRollback = ref(false)
const forceRollbackDetails = ref(null)

// Diff viewer state
const compareMode = ref('working')
const baseCommitId = ref(null)
const compareCommitId = ref(null)
const diffBaseText = ref('')
const diffCompareText = ref('')
const diffBaseLabel = ref('')
const diffCompareLabel = ref('')
const diffError = ref('')
const baselineSnapshot = ref('')
const baselineCommitId = ref(null)
const baselineCommitMessage = ref('')
const commitSnapshotCache = new Map()
let workingSyncTimer = null

const INITIAL_BASE = '__initial__'

// Computed
const allSelected = computed(() =>
  changedFiles.value.length > 0 && selectedFiles.value.length === changedFiles.value.length
)

const someSelected = computed(() =>
  selectedFiles.value.length > 0 && selectedFiles.value.length < changedFiles.value.length
)

const totalInsertions = computed(() =>
  changedFiles.value
    .filter(f => selectedFiles.value.includes(f.id))
    .reduce((sum, f) => sum + (f.insertions || 0), 0)
)

const totalDeletions = computed(() =>
  changedFiles.value
    .filter(f => selectedFiles.value.includes(f.id))
    .reduce((sum, f) => sum + (f.deletions || 0), 0)
)

const canSubmitCommit = computed(() => {
  return props.canCommit &&
         commitMessage.value.trim().length > 0 &&
         selectedFiles.value.length > 0
})

// Commit options for diff selector
const commitOptions = computed(() => recentCommits.value.map((c) => ({
  title: `#${c.id} · ${c.message}`,
  value: c.id
})))

const baseCommitOptions = computed(() => [
  { title: t('workspaceGit.diff.initial'), value: INITIAL_BASE },
  ...commitOptions.value
])

// Helper functions
function authHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function formatDate(iso) {
  if (!iso) return '—'
  try {
    const date = new Date(iso)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return t('workspaceGit.relative.justNow')
    if (diffMins < 60) return t('workspaceGit.relative.minutesAgo', { count: diffMins })
    if (diffHours < 24) return t('workspaceGit.relative.hoursAgo', { count: diffHours })
    if (diffDays < 7) return t('workspaceGit.relative.daysAgo', { count: diffDays })
    return date.toLocaleDateString(locale.value || undefined, { day: '2-digit', month: '2-digit', year: '2-digit' })
  } catch {
    return iso
  }
}

function getFileIcon(path) {
  const ext = path.split('.').pop()?.toLowerCase()
  switch (ext) {
    case 'tex': return 'mdi-file-document'
    case 'bib': return 'mdi-book-open-variant'
    case 'sty': return 'mdi-file-cog'
    case 'cls': return 'mdi-file-settings'
    default: return 'mdi-file-document-outline'
  }
}

function getFileIconColor(path) {
  const ext = path.split('.').pop()?.toLowerCase()
  switch (ext) {
    case 'tex': return 'green'
    case 'bib': return 'blue'
    case 'sty': return 'orange'
    case 'cls': return 'purple'
    default: return 'grey'
  }
}

// Selection functions
function toggleFile(fileId) {
  const index = selectedFiles.value.indexOf(fileId)
  if (index === -1) {
    selectedFiles.value.push(fileId)
  } else {
    selectedFiles.value.splice(index, 1)
  }
}

function toggleSelectAll(value) {
  if (value) {
    selectedFiles.value = changedFiles.value.map(f => f.id)
  } else {
    selectedFiles.value = []
  }
}

function selectAll() {
  selectedFiles.value = changedFiles.value.map(f => f.id)
}

function deselectAll() {
  selectedFiles.value = []
}

// Rollback functions
function confirmRollback(file) {
  rollbackTarget.value = file
  forceRollback.value = false
  forceRollbackDetails.value = null
  showRollbackConfirm.value = true
}

function cancelRollback() {
  rollbackTarget.value = null
  forceRollback.value = false
  forceRollbackDetails.value = null
  showRollbackConfirm.value = false
}

async function executeRollback() {
  if (!rollbackTarget.value) return

  const file = rollbackTarget.value
  rollingBack.value = file.id
  showRollbackConfirm.value = false

  try {
    if (typeof props.beforeRollback === 'function') {
      await props.beforeRollback(file.id)
    }

    const res = await axios.post(
      `${API_BASE}${props.apiPrefix}/documents/${file.id}/rollback`,
      forceRollback.value ? { force: true } : {},
      { headers: authHeaders() }
    )

    // Emit rollback event so parent can refresh the editor
    emit('rollback', { documentId: file.id, baseline: res?.data?.baseline ?? null })

    // Refresh changes list
    await checkForChanges()
  } catch (e) {
    const details = e?.response?.data?.details
    if (details?.requires_force && !forceRollback.value) {
      forceRollback.value = true
      forceRollbackDetails.value = details
      showRollbackConfirm.value = true
      return
    }
    commitError.value = e?.response?.data?.error || e?.message || t('workspaceGit.errors.rollbackFailed')
  } finally {
    rollingBack.value = null
    if (!showRollbackConfirm.value) {
      rollbackTarget.value = null
      forceRollback.value = false
      forceRollbackDetails.value = null
    }
  }
}

// API functions
async function checkForChanges() {
  if (!props.workspaceId) return

  checkingChanges.value = true
  loadError.value = ''

  try {
    // Backend uses database content (synced via YJS)
    const res = await axios.get(
      `${API_BASE}${props.apiPrefix}/workspaces/${props.workspaceId}/changes`,
      { headers: authHeaders() }
    )

    changedFiles.value = res.data.changed_files || []
    deletedFiles.value = res.data.deleted_files || []

    // Auto-select all changed files
    selectedFiles.value = changedFiles.value.map(f => f.id)
  } catch (e) {
    loadError.value = e?.response?.data?.error || e?.message || t('workspaceGit.errors.loadChangesFailed')
    changedFiles.value = []
    deletedFiles.value = []
    selectedFiles.value = []
  } finally {
    checkingChanges.value = false
  }
}

async function restoreFile(file) {
  if (!file || restoringFile.value) return

  restoringFile.value = file.id

  try {
    await axios.post(
      `${API_BASE}${props.apiPrefix}/documents/${file.id}/restore`,
      {},
      { headers: authHeaders() }
    )

    // Refresh changes list
    await checkForChanges()

    // Emit event so parent can refresh the tree
    emit('restored', file.id)
  } catch (e) {
    loadError.value = e?.response?.data?.error || e?.message || t('workspaceGit.errors.restoreFailed')
  } finally {
    restoringFile.value = null
  }
}

function getStatusBadge(file) {
  if (file.status === 'D') return { text: 'D', color: 'error', tooltip: t('workspaceGit.status.deleted') }
  if (file.status === 'A' || !file.has_baseline) return { text: 'A', color: 'info', tooltip: t('workspaceGit.status.added') }
  return { text: 'M', color: 'warning', tooltip: t('workspaceGit.status.modified') }
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

async function fetchCommitSnapshot(commitId) {
  if (!commitId || commitId === INITIAL_BASE) return ''
  if (!props.selectedDocumentId) return ''
  if (commitSnapshotCache.has(commitId)) {
    return commitSnapshotCache.get(commitId) || ''
  }
  const res = await axios.get(
    `${API_BASE}${props.apiPrefix}/documents/${props.selectedDocumentId}/commits/${commitId}`,
    { headers: authHeaders() }
  )
  const snapshot = res.data?.commit?.content_snapshot || ''
  commitSnapshotCache.set(commitId, snapshot)
  return snapshot
}

function syncWorkingDiffText() {
  if (compareMode.value !== 'working') return
  if (workingSyncTimer) clearTimeout(workingSyncTimer)
  workingSyncTimer = setTimeout(() => {
    diffCompareText.value = props.getContent ? String(props.getContent() || '') : ''
  }, 120)
}

async function refreshDiff(force = false) {
  if (!props.selectedDocumentId) {
    diffBaseText.value = ''
    diffCompareText.value = ''
    diffBaseLabel.value = t('workspaceGit.diff.noDocument')
    diffCompareLabel.value = t('workspaceGit.diff.emptyLabel')
    return
  }

  await withLoading('diff', async () => {
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
    }
  })
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
  if (workingSyncTimer) {
    clearTimeout(workingSyncTimer)
    workingSyncTimer = null
  }
}

async function loadRecentCommits() {
  if (!props.workspaceId) return

  loadingCommits.value = true
  try {
    // Get commits from all documents - we'll aggregate them
    const res = await axios.get(
      `${API_BASE}${props.apiPrefix}/workspaces/${props.workspaceId}/tree`,
      { headers: authHeaders() }
    )

    const nodes = res.data.nodes || []
    const textFiles = nodes.filter(n => n.type === 'file' && !n.asset_id)

    // Get commits from first few files
    const commitPromises = textFiles.slice(0, 5).map(async (node) => {
      try {
        const commitRes = await axios.get(
          `${API_BASE}${props.apiPrefix}/documents/${node.id}/commits`,
          { headers: authHeaders() }
        )
        return commitRes.data.commits || []
      } catch {
        return []
      }
    })

    const allCommits = (await Promise.all(commitPromises)).flat()

    // Deduplicate by message + timestamp (grouped commits have same message)
    const uniqueCommits = []
    const seen = new Set()
    for (const c of allCommits.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))) {
      const key = `${c.message}|${c.created_at}`
      if (!seen.has(key)) {
        seen.add(key)
        // Count how many files in this commit group
        const sameCommits = allCommits.filter(cc =>
          cc.message === c.message && cc.created_at === c.created_at
        )
        uniqueCommits.push({ ...c, file_count: sameCommits.length })
      }
    }

    recentCommits.value = uniqueCommits.slice(0, 10)
  } catch (e) {
    console.error('Failed to load recent commits:', e)
    recentCommits.value = []
  } finally {
    loadingCommits.value = false
  }
}

async function submitCommit() {
  if (!canSubmitCommit.value) return

  committing.value = true
  commitError.value = ''

  try {
    if (typeof props.beforeCommit === 'function') {
      await props.beforeCommit([...selectedFiles.value])
    }

    // Backend uses database content (synced via YJS)
    await axios.post(
      `${API_BASE}${props.apiPrefix}/workspaces/${props.workspaceId}/commit`,
      {
        message: commitMessage.value.trim(),
        document_ids: selectedFiles.value
      },
      { headers: authHeaders() }
    )

    commitMessage.value = ''
    selectedFiles.value = []
    changedFiles.value = []
    emit('committed')

    // Reload data
    await Promise.all([checkForChanges(), loadRecentCommits()])
  } catch (e) {
    commitError.value = e?.response?.data?.error || e?.message || t('workspaceGit.errors.commitFailed')
  } finally {
    committing.value = false
  }
}

// Socket handling
let socket = null
let onSocketConnect = null

function handleCommitCreated() {
  // Refresh on any commit
  checkForChanges()
  loadRecentCommits()
}

function setupSocket() {
  socket = getSocket()
  if (!socket) return

  socket.on('latex_collab:commit_created', handleCommitCreated)

  onSocketConnect = () => {
    socket.emit('latex_collab:subscribe_workspace', { workspace_id: props.workspaceId })
  }

  if (socket.connected) {
    onSocketConnect()
  }
  socket.on('connect', onSocketConnect)
}

function cleanupSocket() {
  if (!socket) return
  socket.off('latex_collab:commit_created', handleCommitCreated)
  if (onSocketConnect) socket.off('connect', onSocketConnect)
  if (props.workspaceId) {
    socket.emit('latex_collab:unsubscribe_workspace', { workspace_id: props.workspaceId })
  }
  onSocketConnect = null
}

// Watchers
watch(() => props.workspaceId, async (newId, oldId) => {
  if (oldId && oldId !== newId) {
    cleanupSocket()
  }
  changedFiles.value = []
  selectedFiles.value = []
  commitMessage.value = ''
  recentCommits.value = []
  resetDiffState()

  if (newId) {
    await Promise.all([checkForChanges(), loadRecentCommits()])
    setupSocket()
  }
})

// Watch for document changes to refresh diff
watch(() => props.selectedDocumentId, async (newId, oldId) => {
  if (newId !== oldId) {
    resetDiffState()
    if (newId && fullscreen.value) {
      await refreshDiff(true)
    }
  }
})

// Watch compare mode changes
watch(compareMode, async () => {
  await refreshDiff(false)
})

// Watch commit selection changes
watch([baseCommitId, compareCommitId], async () => {
  if (compareMode.value === 'commit-range') {
    await refreshDiff(false)
  }
})

// Watch fullscreen to load diff when opening
watch(fullscreen, async (isFullscreen) => {
  if (isFullscreen && props.selectedDocumentId) {
    await refreshDiff(true)
  }
})

// Lifecycle
onMounted(async () => {
  if (props.workspaceId) {
    await Promise.all([checkForChanges(), loadRecentCommits()])
    setupSocket()
  }
})

onUnmounted(() => {
  cleanupSocket()
  resetDiffState()
})

// Expose method for parent to trigger refresh
defineExpose({
  checkForChanges,
  refresh: async () => {
    await Promise.all([checkForChanges(), loadRecentCommits()])
  }
})
</script>

<style scoped>
/* LLARS Design Variables */
.git-panel-wrapper {
  --llars-primary: #b0ca97;
  --llars-secondary: #D1BC8A;
  --llars-accent: #88c4c8;
  --llars-success: #98d4bb;
  --llars-warning: #e8c87a;
  --llars-danger: #e8a087;
  --llars-gray: #9e9e9e;
  --llars-radius: 16px 4px 16px 4px;
  --llars-radius-sm: 8px 2px 8px 2px;
}

/* ============================================
   COLLAPSED STATE
   ============================================ */
.git-panel-collapsed {
  background: linear-gradient(135deg, var(--llars-primary) 0%, var(--llars-accent) 100%);
  border-radius: var(--llars-radius-sm);
  padding: 6px 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.git-panel-collapsed:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.collapsed-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.collapsed-icon-box {
  width: 28px;
  height: 28px;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 6px 2px 6px 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.collapsed-label {
  font-weight: 600;
  font-size: 13px;
  color: white;
}

.expand-icon {
  color: white;
  opacity: 0.8;
}

/* ============================================
   EXPANDED STATE
   ============================================ */
.git-panel-expanded {
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.panel-header {
  background: linear-gradient(135deg, var(--llars-primary) 0%, var(--llars-accent) 100%);
  padding: 10px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon-box {
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 8px 2px 8px 2px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-icon-box.large {
  width: 40px;
  height: 40px;
}

.header-title {
  font-weight: 600;
  font-size: 15px;
  color: white;
}

.header-actions {
  display: flex;
  gap: 2px;
}

.header-actions .v-btn {
  color: white !important;
}

.panel-content {
  padding: 16px;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.section-title {
  font-weight: 600;
  font-size: 13px;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 10px;
  display: flex;
  align-items: center;
}

.file-count, .file-count-header {
  font-weight: 400;
  font-size: 12px;
  color: rgb(var(--v-theme-on-surface-variant));
}

/* Files Section */
.files-section {
  display: flex;
  flex-direction: column;
}

.empty-files {
  color: rgb(var(--v-theme-on-surface-variant));
  font-size: 13px;
  text-align: center;
  padding: 20px;
}

.file-list {
  max-height: 200px;
  overflow-y: auto;
}

.select-all-row {
  padding: 4px 0;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  margin-bottom: 4px;
}

.select-all-label {
  font-size: 12px;
  font-weight: 500;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 4px;
  border-radius: 4px;
  transition: background 0.15s;
}

.file-item:hover {
  background: rgba(var(--v-theme-primary), 0.05);
}

.file-item.selected {
  background: rgba(var(--v-theme-primary), 0.1);
}

.file-icon {
  flex-shrink: 0;
}

.file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.file-path {
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-stats {
  font-size: 11px;
  font-family: monospace;
  white-space: nowrap;
}

/* Commit Section */
.commit-section {
  display: flex;
  flex-direction: column;
}

.commit-input :deep(.v-field) {
  border-radius: var(--llars-radius-sm) !important;
}

.commit-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

/* ============================================
   FULLSCREEN STATE
   ============================================ */
.git-fullscreen {
  background: rgb(var(--v-theme-background));
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.fullscreen-header {
  background: linear-gradient(135deg, var(--llars-primary) 0%, var(--llars-accent) 100%);
  padding: 16px 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.fullscreen-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.fullscreen-grid {
  display: grid;
  grid-template-columns: 300px 350px 1fr;
  gap: 24px;
  height: calc(100vh - 120px);
}

.fullscreen-left,
.fullscreen-middle,
.fullscreen-right {
  display: flex;
  flex-direction: column;
}

/* Git Card */
.git-card {
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  flex: 1;
}

.card-header {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  font-weight: 600;
  font-size: 14px;
  display: flex;
  align-items: center;
}

.card-content {
  padding: 16px;
  flex: 1;
  overflow-y: auto;
}

/* Bulk Actions */
.bulk-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* File List Full */
.file-list-full {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-item-full {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--llars-radius-sm);
  cursor: pointer;
  transition: background 0.15s;
}

.file-item-full:hover {
  background: rgba(var(--v-theme-primary), 0.05);
}

.file-item-full.selected {
  background: rgba(var(--v-theme-primary), 0.12);
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-path-full {
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 2px;
}

.file-stats-full {
  display: flex;
  gap: 8px;
  align-items: center;
}

.stat-badge {
  font-size: 11px;
  font-family: monospace;
  padding: 1px 6px;
  border-radius: 4px;
}

.stat-badge.success {
  background: rgba(152, 212, 187, 0.2);
  color: #2e7d32;
}

.stat-badge.error {
  background: rgba(232, 160, 135, 0.2);
  color: #c62828;
}

.new-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(136, 196, 200, 0.2);
  color: #0288d1;
  text-transform: uppercase;
}

/* Commit Summary */
.commit-summary {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.no-selection {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px;
  color: rgb(var(--v-theme-on-surface-variant));
  font-size: 13px;
}

.commit-textarea :deep(.v-field) {
  border-radius: var(--llars-radius-sm) !important;
}

/* History */
.history-content {
  padding: 8px !important;
  max-height: 300px;
}

.history-list-full {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.history-item-full {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--llars-radius-sm);
}

.commit-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--llars-primary);
  flex-shrink: 0;
}

.commit-details {
  flex: 1;
  min-width: 0;
}

.commit-message-full {
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.commit-meta-full {
  font-size: 11px;
  color: rgb(var(--v-theme-on-surface-variant));
  display: flex;
  gap: 8px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: rgb(var(--v-theme-on-surface-variant));
  font-size: 13px;
}

.empty-state.small {
  padding: 20px;
}

/* Rollback Confirm Dialog */
.rollback-confirm-card {
  border-radius: var(--llars-radius) !important;
}

.rollback-confirm-card .v-card-title {
  font-size: 16px;
  font-weight: 600;
  padding-bottom: 8px;
}

/* Commit count */
.commit-count {
  font-weight: 400;
  font-size: 12px;
  color: rgb(var(--v-theme-on-surface-variant));
}

/* History item active state */
.history-item-full {
  cursor: pointer;
}

.history-item-full.active {
  background: rgba(var(--v-theme-primary), 0.15);
}

.history-item-full.active .commit-indicator {
  background: var(--llars-accent);
  box-shadow: 0 0 0 3px rgba(136, 196, 200, 0.3);
}

/* Mode toggle */
.mode-toggle {
  border-radius: var(--llars-radius-sm) !important;
}

.mode-toggle .v-btn {
  font-size: 11px !important;
  text-transform: none !important;
}

/* Diff Section */
.diff-content {
  display: flex;
  flex-direction: column;
}

.diff-selectors {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.diff-selectors .v-select {
  flex: 1;
}

.no-document-selected {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: rgb(var(--v-theme-on-surface-variant));
  font-size: 13px;
  text-align: center;
}

.diff-viewer-full {
  flex: 1;
  min-height: 0;
}

/* Responsive */
@media (max-width: 1400px) {
  .fullscreen-grid {
    grid-template-columns: 280px 300px 1fr;
  }
}

@media (max-width: 1200px) {
  .fullscreen-grid {
    grid-template-columns: 1fr 1fr;
  }

  .fullscreen-right {
    grid-column: span 2;
  }
}

@media (max-width: 768px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .fullscreen-grid {
    grid-template-columns: 1fr;
  }

  .fullscreen-right {
    grid-column: span 1;
  }
}

/* Status Badges */
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

.status-badge-full {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  font-size: 11px;
  font-weight: 700;
  border-radius: 4px;
  flex-shrink: 0;
}

.status-badge-full.warning {
  background: rgba(232, 200, 122, 0.25);
  color: #f9a825;
}

.status-badge-full.info {
  background: rgba(136, 196, 200, 0.25);
  color: #0288d1;
}

.status-badge-full.error {
  background: rgba(232, 160, 135, 0.25);
  color: #c62828;
}

/* Deleted Files Section */
.deleted-section-title {
  font-size: 11px;
  font-weight: 600;
  color: rgb(var(--v-theme-error));
  display: flex;
  align-items: center;
  padding: 6px 4px;
  margin-top: 4px;
}

.deleted-section-header {
  font-size: 12px;
  font-weight: 600;
  color: rgb(var(--v-theme-error));
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin-top: 8px;
  margin-bottom: 4px;
}

.file-item.deleted {
  opacity: 0.85;
  background: rgba(232, 160, 135, 0.08);
}

.file-item-full.deleted {
  opacity: 0.85;
  background: rgba(232, 160, 135, 0.08);
}

.deleted-path {
  text-decoration: line-through;
  color: rgb(var(--v-theme-error));
}

.deleted-text {
  text-decoration: line-through;
  color: rgb(var(--v-theme-error));
}

.deleted-date {
  font-size: 11px;
  color: rgb(var(--v-theme-on-surface-variant));
}

/* Deleted Files Card (fullscreen) */
.deleted-header {
  border-bottom-color: rgba(232, 160, 135, 0.3);
}

.deleted-count {
  font-weight: 400;
  font-size: 12px;
  color: rgb(var(--v-theme-error));
}

.deleted-files-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.deleted-file-item {
  display: flex;
  align-items: center;
  padding: 8px 10px;
  background: rgba(232, 160, 135, 0.08);
  border-radius: var(--llars-radius-sm);
}

.deleted-file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.deleted-file-name {
  font-size: 13px;
  font-weight: 500;
  text-decoration: line-through;
  color: rgb(var(--v-theme-error));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.deleted-file-date {
  font-size: 11px;
  color: rgb(var(--v-theme-on-surface-variant));
}
</style>
