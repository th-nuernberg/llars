<template>
  <!-- Tree Collapsed State: Just icon + badge -->
  <div v-if="treeCollapsed" class="git-widget-icon" @click="$emit('open-detail')">
    <LIcon size="20">mdi-source-branch</LIcon>
    <span v-if="totalChanges > 0" class="git-badge">{{ totalChanges }}</span>
  </div>

  <!-- Widget Collapsed State -->
  <div
    v-else-if="collapsed"
    class="git-widget-collapsed"
    @click="$emit('update:collapsed', false)"
  >
    <LIcon size="16" class="branch-icon">mdi-source-branch</LIcon>
    <span class="branch-name">main</span>
    <LTag v-if="totalChanges > 0" variant="warning" size="sm">
      {{ totalChanges }}
    </LTag>
    <v-spacer />
    <LIcon size="14" class="expand-icon">mdi-chevron-down</LIcon>
  </div>

  <!-- Widget Expanded State -->
  <div v-else class="git-widget-expanded">
    <!-- Header -->
    <div class="widget-header">
      <LIcon size="16">mdi-source-branch</LIcon>
      <span class="header-title">Git</span>
      <v-spacer />
      <LIconBtn
        icon="mdi-open-in-new"
        size="x-small"
        :tooltip="$t('workspaceGit.openDetail')"
        @click="$emit('open-detail')"
      />
      <LIconBtn
        icon="mdi-chevron-up"
        size="x-small"
        :tooltip="$t('common.collapse')"
        @click="$emit('update:collapsed', true)"
      />
    </div>

    <!-- Status Row -->
    <div class="widget-status">
      <LTag variant="info" size="sm">main</LTag>
      <LTag v-if="changedCount > 0" variant="warning" size="sm">
        {{ changedCount }} {{ $t('workspaceGit.changed') }}
      </LTag>
      <LTag v-if="deletedCount > 0" variant="danger" size="sm">
        {{ deletedCount }} {{ $t('workspaceGit.deleted') }}
      </LTag>
      <LIconBtn
        v-if="!checkingChanges"
        icon="mdi-refresh"
        size="x-small"
        :tooltip="$t('workspaceGit.refresh')"
        @click="refresh"
      />
      <LIcon v-else size="14" class="mdi-spin text-medium-emphasis">mdi-loading</LIcon>
    </div>

    <!-- Quick Commit -->
    <div v-if="changedCount > 0 && canCommit" class="widget-commit">
      <v-text-field
        v-model="quickMessage"
        density="compact"
        variant="outlined"
        :placeholder="$t('workspaceGit.commitPlaceholder')"
        hide-details
        class="commit-input"
        @keyup.enter="handleQuickCommit"
      />
      <LBtn
        variant="primary"
        size="small"
        :loading="committing"
        :disabled="!quickMessage.trim() || committing"
        @click="handleQuickCommit"
      >
        {{ $t('workspaceGit.commit') }}
      </LBtn>
    </div>

    <!-- File Preview -->
    <div v-if="previewFiles.length > 0" class="widget-files">
      <div
        v-for="file in previewFiles"
        :key="file.id"
        class="file-row"
      >
        <LIcon size="14" :color="getFileIconColor(file.path)">
          {{ getFileIcon(file.path) }}
        </LIcon>
        <span class="file-name">{{ file.title || file.path }}</span>
        <LTag :variant="getStatusBadge(file).color" size="sm">
          {{ getStatusBadge(file).text }}
        </LTag>
        <span v-if="file.insertions || file.deletions" class="file-stats">
          <span v-if="file.insertions" class="insertions">+{{ file.insertions }}</span>
          <span v-if="file.deletions" class="deletions">-{{ file.deletions }}</span>
        </span>
      </div>
      <div v-if="moreFilesCount > 0" class="more-files" @click="$emit('open-detail')">
        +{{ moreFilesCount }} {{ $t('workspaceGit.moreFiles') }}
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!checkingChanges" class="widget-empty">
      <LIcon size="16" class="text-medium-emphasis">mdi-check-circle</LIcon>
      <span class="text-medium-emphasis">{{ $t('workspaceGit.noChanges') }}</span>
    </div>

    <!-- Error -->
    <div v-if="commitError" class="widget-error">
      <LIcon size="14" color="error">mdi-alert-circle</LIcon>
      <span>{{ commitError }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, toRef } from 'vue'
import { useGitStatus } from '@/composables/useGitStatus'

const MAX_PREVIEW_FILES = 5

const props = defineProps({
  workspaceId: { type: Number, required: true },
  collapsed: { type: Boolean, default: true },
  treeCollapsed: { type: Boolean, default: false },
  canCommit: { type: Boolean, default: false },
  apiPrefix: { type: String, default: '/api/latex-collab' }
})

const emit = defineEmits(['update:collapsed', 'open-detail', 'committed'])

// Use shared git status composable
const workspaceIdRef = toRef(props, 'workspaceId')
const {
  changedFiles,
  deletedFiles,
  checkingChanges,
  committing,
  commitError,
  changedCount,
  deletedCount,
  totalChanges,
  getFileIcon,
  getFileIconColor,
  getStatusBadge,
  quickCommit,
  refresh
} = useGitStatus(workspaceIdRef, {
  apiPrefix: props.apiPrefix,
  autoSetup: true
})

// Local state for quick commit
const quickMessage = ref('')

// Computed
const previewFiles = computed(() => changedFiles.value.slice(0, MAX_PREVIEW_FILES))
const moreFilesCount = computed(() => Math.max(0, changedFiles.value.length - MAX_PREVIEW_FILES))

// Methods
async function handleQuickCommit() {
  if (!quickMessage.value.trim() || committing.value) return

  const success = await quickCommit(quickMessage.value)
  if (success) {
    quickMessage.value = ''
    emit('committed')
  }
}
</script>

<style scoped>
/* Tree Collapsed - Icon only */
.git-widget-icon {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 0;
  cursor: pointer;
  transition: all 0.2s ease;
}

.git-widget-icon:hover {
  color: var(--llars-primary);
}

.git-badge {
  font-size: 10px;
  font-weight: 600;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: rgb(var(--v-theme-warning));
  color: white;
}

/* Widget Collapsed */
.git-widget-collapsed {
  flex-shrink: 0;
  height: 36px;
  padding: 0 10px;
  display: flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg,
    rgba(176, 202, 151, 0.12),
    rgba(136, 196, 200, 0.12));
  border-radius: 6px 2px 6px 2px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.git-widget-collapsed:hover {
  background: linear-gradient(135deg,
    rgba(176, 202, 151, 0.22),
    rgba(136, 196, 200, 0.22));
}

.branch-icon {
  color: var(--llars-primary);
}

.branch-name {
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.expand-icon {
  opacity: 0.5;
  transition: opacity 0.2s ease;
}

.git-widget-collapsed:hover .expand-icon {
  opacity: 1;
}

/* Widget Expanded */
.git-widget-expanded {
  flex: 1;
  min-height: 120px;
  max-height: 280px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 8px 2px 8px 2px;
  background: rgb(var(--v-theme-surface));
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.widget-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.header-title {
  font-size: 0.8rem;
  font-weight: 600;
}

.widget-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.widget-commit {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.commit-input {
  flex: 1;
}

.commit-input :deep(.v-field) {
  font-size: 0.75rem;
}

.commit-input :deep(.v-field__input) {
  padding: 4px 8px;
  min-height: 28px;
}

.widget-files {
  flex: 1;
  overflow-y: auto;
  padding: 6px 0;
}

.file-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  font-size: 0.75rem;
}

.file-row:hover {
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.file-stats {
  display: flex;
  gap: 4px;
  font-size: 0.65rem;
  font-weight: 500;
}

.insertions {
  color: rgb(var(--v-theme-success));
}

.deletions {
  color: rgb(var(--v-theme-error));
}

.more-files {
  padding: 6px 10px;
  font-size: 0.7rem;
  color: var(--llars-accent);
  cursor: pointer;
  transition: color 0.2s ease;
}

.more-files:hover {
  color: var(--llars-primary);
}

.widget-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 16px;
  font-size: 0.75rem;
}

.widget-error {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  font-size: 0.7rem;
  color: rgb(var(--v-theme-error));
  background: rgba(var(--v-theme-error), 0.08);
}
</style>
