<!--
  GitPanelContent.vue

  Git status content for the tree stack panel.
  Shows changed files, quick commit, and status without its own header.
-->
<template>
  <div class="git-panel-content">
    <!-- Status Row -->
    <div class="git-status-row">
      <LTag variant="info" size="sm">main</LTag>
      <LTag v-if="changedCount > 0" variant="warning" size="sm">
        {{ changedCount }} {{ $t('workspaceGit.changed') }}
      </LTag>
      <LTag v-if="deletedCount > 0" variant="danger" size="sm">
        {{ deletedCount }} {{ $t('workspaceGit.deleted') }}
      </LTag>
      <v-spacer />
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
    <div v-if="changedCount > 0 && canCommit" class="git-commit-row">
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

    <!-- File List -->
    <div class="git-files-list">
      <div
        v-for="file in changedFiles"
        :key="file.id"
        class="git-file-row"
        :class="{ 'has-rename': file.old_title || file.old_path }"
      >
        <LIcon size="14" :color="getFileIconColor(file.path)">
          {{ getFileIcon(file.path) }}
        </LIcon>
        <div class="file-info">
          <span class="file-name">{{ file.title || file.path }}</span>
          <span v-if="file.old_title" class="file-old-name">
            ← {{ file.old_title }}
          </span>
          <span v-else-if="file.old_path" class="file-old-name">
            ← {{ file.old_path }}
          </span>
        </div>
        <LTag :variant="getStatusBadge(file).color" size="sm" :title="getStatusBadge(file).tooltip">
          {{ getStatusBadge(file).text }}
        </LTag>
        <span v-if="file.insertions || file.deletions" class="file-stats">
          <span v-if="file.insertions" class="insertions">+{{ file.insertions }}</span>
          <span v-if="file.deletions" class="deletions">-{{ file.deletions }}</span>
        </span>
      </div>

      <!-- Deleted Files -->
      <div
        v-for="file in deletedFiles"
        :key="`del-${file.id}`"
        class="git-file-row deleted"
      >
        <LIcon size="14" color="error">mdi-file-remove</LIcon>
        <span class="file-name">{{ file.title || file.path }}</span>
        <LTag variant="danger" size="sm">D</LTag>
      </div>

      <!-- Empty State -->
      <div v-if="!checkingChanges && totalChanges === 0" class="git-empty">
        <LIcon size="16" class="text-medium-emphasis">mdi-check-circle</LIcon>
        <span class="text-medium-emphasis">{{ $t('workspaceGit.noChanges') }}</span>
      </div>
    </div>

    <!-- Error -->
    <div v-if="commitError" class="git-error">
      <LIcon size="14" color="error">mdi-alert-circle</LIcon>
      <span>{{ commitError }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, toRef, watch } from 'vue'
import { useGitStatus } from '@/composables/useGitStatus'

const props = defineProps({
  workspaceId: { type: Number, required: true },
  canCommit: { type: Boolean, default: false },
  apiPrefix: { type: String, default: '/api/latex-collab' }
})

const emit = defineEmits(['open-detail', 'committed', 'total-changes'])

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

// Emit total changes for badge
watch(totalChanges, (val) => {
  emit('total-changes', val)
}, { immediate: true })

const quickMessage = ref('')

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
.git-panel-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.git-status-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  flex-shrink: 0;
}

.git-commit-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  flex-shrink: 0;
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

.git-files-list {
  flex: 1;
  overflow-y: auto;
  padding: 6px 0;
}

.git-file-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  font-size: 0.75rem;
}

.git-file-row:hover {
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.git-file-row.deleted {
  opacity: 0.7;
}

.file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.file-old-name {
  font-size: 0.65rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.git-file-row.has-rename {
  padding-top: 6px;
  padding-bottom: 6px;
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

.git-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 16px;
  font-size: 0.75rem;
}

.git-error {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  font-size: 0.7rem;
  color: rgb(var(--v-theme-error));
  background: rgba(var(--v-theme-error), 0.08);
  flex-shrink: 0;
}
</style>
