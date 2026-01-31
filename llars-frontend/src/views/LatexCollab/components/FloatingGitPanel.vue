<!--
  FloatingGitPanel.vue

  A draggable floating window for Git operations.
  Uses LFloatingWindow for consistent LLARS design.
-->
<template>
  <LFloatingWindow
    :model-value="modelValue"
    :title="$t('workspaceGit.fullscreen.title')"
    icon="mdi-source-branch"
    color="primary"
    :width="800"
    :height="500"
    :min-width="500"
    :min-height="300"
    storage-key="llars-git-panel-state"
    :show-close="true"
    :show-refresh="true"
    :refresh-loading="checkingChanges"
    :refresh-tooltip="$t('workspaceGit.actions.refresh')"
    @update:model-value="$emit('update:modelValue', $event)"
    @refresh="refresh"
    @close="$emit('update:modelValue', false)"
  >
    <!-- Status Tags -->
    <template #tags>
      <LTag v-if="changedCount > 0" variant="warning" size="small">
        {{ changedCount }} {{ $t('workspaceGit.tags.changed', { count: changedCount }) }}
      </LTag>
      <LTag v-if="deletedCount > 0" variant="danger" size="small">
        {{ deletedCount }} {{ $t('workspaceGit.tags.deleted', { count: deletedCount }) }}
      </LTag>
      <LTag v-if="changedCount === 0 && deletedCount === 0" variant="success" size="small">
        {{ $t('workspaceGit.tags.synced') }}
      </LTag>
    </template>

    <!-- Content -->
    <div class="git-panel-content">
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
                size="small"
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
                size="small"
                @update:model-value="toggleFile(file.id)"
                @click.stop
              />
              <LIcon size="14" :color="getFileIconColor(file.path)">
                {{ getFileIcon(file.path) }}
              </LIcon>
              <span class="file-name">{{ file.title || file.path }}</span>
              <LTag :variant="getStatusBadge(file).color" size="small">
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
                size="small"
                @update:model-value="toggleFile(`del-${file.id}`)"
                @click.stop
              />
              <LIcon size="14" color="error">mdi-file-remove</LIcon>
              <span class="file-name deleted-name">{{ file.title }}</span>
              <LTag variant="danger" size="small">D</LTag>
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
    <template #footer>
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
    </template>
  </LFloatingWindow>
</template>

<script setup>
import { ref, computed, watch, toRef } from 'vue'
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

// Watch for open/close
watch(() => props.modelValue, async (isOpen) => {
  if (isOpen) {
    await refresh()
  } else {
    selectedDiffFile.value = null
    diffBaseText.value = ''
    diffCompareText.value = ''
  }
})
</script>

<style scoped>
.git-panel-content {
  height: 100%;
  overflow: hidden;
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
</style>
