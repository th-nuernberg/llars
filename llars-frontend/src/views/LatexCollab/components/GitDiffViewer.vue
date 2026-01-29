<!--
  GitDiffViewer.vue

  Displays unified diff for a single file with syntax highlighting.
  Shows additions in green, deletions in red, and context lines in gray.
-->
<template>
  <div class="git-diff-viewer">
    <!-- Header -->
    <div class="diff-header">
      <div class="diff-file-info">
        <LIcon size="16" :color="getFileIconColor(file?.path)">
          {{ getFileIcon(file?.path) }}
        </LIcon>
        <span class="diff-file-name">{{ file?.title || file?.path || 'Unknown' }}</span>
        <LTag v-if="file?.type === 'deleted'" variant="danger" size="sm">
          {{ $t('workspaceGit.status.deleted') }}
        </LTag>
      </div>
      <div class="diff-stats">
        <span v-if="diffData?.insertions" class="stat-additions">
          +{{ diffData.insertions }}
        </span>
        <span v-if="diffData?.deletions" class="stat-deletions">
          -{{ diffData.deletions }}
        </span>
      </div>
      <LIconBtn
        icon="mdi-close"
        size="x-small"
        :tooltip="$t('common.close')"
        @click="$emit('close')"
      />
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="diff-loading">
      <LLoading :text="$t('workspaceGit.diff.loading')" />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="diff-error">
      <LIcon size="20" color="error">mdi-alert-circle</LIcon>
      <span>{{ error }}</span>
    </div>

    <!-- No Changes -->
    <div v-else-if="diffData && !diffData.has_changes" class="diff-empty">
      <LIcon size="24" class="text-medium-emphasis">mdi-check-circle</LIcon>
      <span>{{ $t('workspaceGit.diff.noChanges') }}</span>
    </div>

    <!-- Diff Content -->
    <div v-else-if="diffData" class="diff-content">
      <div
        v-for="(hunk, hunkIndex) in diffData.diff?.hunks"
        :key="hunkIndex"
        class="diff-hunk"
      >
        <div class="hunk-header">{{ hunk.header }}</div>
        <div class="hunk-lines">
          <div
            v-for="(line, lineIndex) in hunk.lines"
            :key="lineIndex"
            class="diff-line"
            :class="line.type"
          >
            <span class="line-prefix">{{ getLinePrefix(line.type) }}</span>
            <span class="line-content">{{ formatLineContent(line.content) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  file: { type: Object, default: null },
  apiPrefix: { type: String, default: '/api/latex-collab' }
})

defineEmits(['close'])

const loading = ref(false)
const error = ref(null)
const diffData = ref(null)

// File icon helpers (same as in GitPanelContent)
function getFileIcon(path) {
  if (!path) return 'mdi-file'
  const ext = path.split('.').pop()?.toLowerCase()
  const iconMap = {
    tex: 'mdi-file-document',
    bib: 'mdi-book-open-variant',
    cls: 'mdi-file-cog',
    sty: 'mdi-file-cog',
    md: 'mdi-language-markdown',
    txt: 'mdi-file-document-outline'
  }
  return iconMap[ext] || 'mdi-file'
}

function getFileIconColor(path) {
  if (!path) return undefined
  const ext = path.split('.').pop()?.toLowerCase()
  const colorMap = {
    tex: '#4caf50',
    bib: '#2196f3',
    cls: '#ff9800',
    sty: '#ff9800'
  }
  return colorMap[ext]
}

function getLinePrefix(type) {
  switch (type) {
    case 'addition': return '+'
    case 'deletion': return '-'
    default: return ' '
  }
}

function formatLineContent(content) {
  // Remove the first character (the diff prefix +/-/space) if present
  if (content && (content.startsWith('+') || content.startsWith('-') || content.startsWith(' '))) {
    return content.substring(1)
  }
  return content || ''
}

async function fetchDiff(documentId) {
  if (!documentId) {
    diffData.value = null
    return
  }

  loading.value = true
  error.value = null

  try {
    const response = await axios.get(`${props.apiPrefix}/documents/${documentId}/diff`)
    diffData.value = response.data
  } catch (err) {
    console.error('[GitDiffViewer] Failed to fetch diff:', err)
    error.value = err.response?.data?.error || 'Failed to load diff'
    diffData.value = null
  } finally {
    loading.value = false
  }
}

// Watch for file changes
watch(
  () => props.file?.id,
  (newId) => {
    if (newId) {
      fetchDiff(newId)
    } else {
      diffData.value = null
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.git-diff-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: rgba(var(--v-theme-surface), 1);
  border-radius: 8px;
  overflow: hidden;
}

.diff-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
}

.diff-file-info {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.diff-file-name {
  font-weight: 500;
  font-size: 0.85rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.diff-stats {
  display: flex;
  gap: 8px;
  font-size: 0.75rem;
  font-weight: 600;
}

.stat-additions {
  color: rgb(var(--v-theme-success));
}

.stat-deletions {
  color: rgb(var(--v-theme-error));
}

.diff-loading,
.diff-error,
.diff-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px;
  flex: 1;
  font-size: 0.85rem;
}

.diff-error {
  color: rgb(var(--v-theme-error));
}

.diff-content {
  flex: 1;
  overflow-y: auto;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.75rem;
  line-height: 1.5;
}

.diff-hunk {
  margin-bottom: 8px;
}

.hunk-header {
  padding: 4px 12px;
  background: rgba(var(--v-theme-info), 0.1);
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-size: 0.7rem;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.hunk-lines {
  background: rgba(var(--v-theme-on-surface), 0.01);
}

.diff-line {
  display: flex;
  padding: 1px 0;
  border-left: 3px solid transparent;
}

.diff-line.addition {
  background: rgba(var(--v-theme-success), 0.12);
  border-left-color: rgb(var(--v-theme-success));
}

.diff-line.deletion {
  background: rgba(var(--v-theme-error), 0.12);
  border-left-color: rgb(var(--v-theme-error));
}

.diff-line.context {
  background: transparent;
}

.diff-line.info {
  background: rgba(var(--v-theme-warning), 0.08);
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-style: italic;
}

.line-prefix {
  width: 20px;
  padding-left: 8px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  user-select: none;
  flex-shrink: 0;
}

.diff-line.addition .line-prefix {
  color: rgb(var(--v-theme-success));
}

.diff-line.deletion .line-prefix {
  color: rgb(var(--v-theme-error));
}

.line-content {
  flex: 1;
  padding-right: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
