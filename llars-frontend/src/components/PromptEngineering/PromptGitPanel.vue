<template>
  <div class="git-panel-wrapper">
    <!-- Collapsed State: Thin bar -->
    <div v-if="!expanded" class="git-panel-collapsed" @click="expanded = true">
      <div class="collapsed-content">
        <div class="collapsed-icon-box">
          <v-icon size="18">mdi-source-branch</v-icon>
        </div>
        <span class="collapsed-label">Git</span>
        <LTag
          v-if="summary?.hasChanges"
          variant="warning"
          size="small"
        >
          <span class="change-indicator">
            <span class="text-success">+{{ summary?.insertions || 0 }}</span>
            <span class="mx-1">/</span>
            <span class="text-error">-{{ summary?.deletions || 0 }}</span>
          </span>
        </LTag>
        <LTag v-else variant="gray" size="small">
          Keine Änderungen
        </LTag>
        <v-spacer />
        <v-icon size="18" class="expand-icon">mdi-chevron-up</v-icon>
      </div>
    </div>

    <!-- Expanded State: Panel -->
    <div v-if="expanded" class="git-panel-expanded">
      <!-- Header -->
      <div class="panel-header">
        <div class="header-icon-box">
          <v-icon size="20" color="white">mdi-source-branch</v-icon>
        </div>
        <span class="header-title">Git Panel</span>
        <LTag
          v-if="summary?.hasChanges"
          variant="warning"
          size="small"
        >
          +{{ summary?.insertions || 0 }} / -{{ summary?.deletions || 0 }}
        </LTag>
        <LTag v-else variant="success" size="small">
          Synced
        </LTag>
        <v-spacer />
        <div class="header-actions">
          <v-btn
            icon
            variant="text"
            size="small"
            title="Aktualisieren"
            @click="loadCommits(true)"
          >
            <v-icon size="18">mdi-refresh</v-icon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            title="Einklappen"
            @click="expanded = false"
          >
            <v-icon size="18">mdi-chevron-down</v-icon>
          </v-btn>
        </div>
      </div>

      <!-- Content -->
      <div class="panel-content">
        <v-alert v-if="loadError" type="error" variant="tonal" class="mb-3" density="compact">
          {{ loadError }}
        </v-alert>

        <!-- Two columns: Commit + History -->
        <div class="content-grid">
          <!-- Left: Commit Section -->
          <div class="commit-section">
            <div class="section-title">
              <v-icon size="16" class="mr-1">mdi-pencil-plus</v-icon>
              Änderungen committen
            </div>

            <!-- User changes summary -->
            <div v-if="(summary?.users || []).length > 0" class="user-changes">
              <div
                v-for="u in summary.users"
                :key="u.username"
                class="user-change-item"
              >
                <span class="user-dot" :style="{ backgroundColor: u.color }" />
                <span class="user-name">{{ u.username }}</span>
                <span class="user-lines">{{ u.changedLines }} Zeilen</span>
              </div>
            </div>

            <v-alert v-if="commitError" type="error" variant="tonal" class="mb-2" density="compact">
              {{ commitError }}
            </v-alert>

            <v-text-field
              v-model="commitMessage"
              placeholder="Commit Message eingeben..."
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
                @click="submitCommit"
              >
                Commit
              </LBtn>
            </div>
          </div>

          <!-- Right: History Section -->
          <div class="history-section">
            <div class="section-title">
              <v-icon size="16" class="mr-1">mdi-history</v-icon>
              History ({{ commits.length }})
            </div>

            <v-skeleton-loader v-if="isLoading('commits')" type="list-item@4" />
            <div v-else-if="commits.length === 0" class="empty-history">
              Noch keine Commits
            </div>
            <div v-else class="history-list">
              <div
                v-for="c in commits.slice(0, 8)"
                :key="c.id"
                class="history-item"
              >
                <div class="commit-indicator" />
                <div class="commit-info">
                  <span class="commit-message">{{ c.message }}</span>
                  <span class="commit-meta">{{ c.author }} · {{ formatDate(c.created_at) }}</span>
                </div>
                <LTag variant="gray" size="small">#{{ c.id }}</LTag>
              </div>
              <div v-if="commits.length > 8" class="more-commits">
                +{{ commits.length - 8 }} weitere Commits
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import axios from 'axios'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'
import { getSocket } from '@/services/socketService'

const props = defineProps({
  promptId: { type: Number, required: true },
  summary: { type: Object, default: () => ({ users: [], totalChangedLines: 0, hasChanges: false, insertions: 0, deletions: 0 }) },
  canCommit: { type: Boolean, default: true },
  getContent: { type: Function, default: null }
})

const emit = defineEmits(['committed'])

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080'
const { isLoading, withLoading } = useSkeletonLoading(['commits'])

const expanded = ref(false)
const commits = ref([])
const commitMessage = ref('')
const committing = ref(false)
const commitError = ref('')
const loadError = ref('')

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

    if (diffMins < 1) return 'Gerade eben'
    if (diffMins < 60) return `vor ${diffMins} Min.`
    if (diffHours < 24) return `vor ${diffHours} Std.`
    if (diffDays < 7) return `vor ${diffDays} Tagen`
    return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: '2-digit' })
  } catch {
    return iso
  }
}

async function loadCommits(force = false) {
  await withLoading('commits', async () => {
    loadError.value = ''
    try {
      const res = await axios.get(`${API_BASE}/api/prompts/${props.promptId}/commits`, {
        headers: authHeaders(),
        params: force ? { _ts: Date.now() } : undefined
      })
      commits.value = res.data.commits || []
    } catch (e) {
      commits.value = []
      loadError.value = e?.response?.data?.error || e?.message || 'History konnte nicht geladen werden'
    }
  })
}

const canSubmitCommit = computed(() => {
  const msgOk = commitMessage.value.trim().length > 0
  const hasChanges = props.summary?.hasChanges === true || (props.summary?.totalChangedLines || 0) > 0
  return props.canCommit && msgOk && hasChanges
})

async function submitCommit() {
  if (!canSubmitCommit.value) return
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
    await loadCommits(true)
    emit('committed')
  } catch (e) {
    commitError.value = e?.response?.data?.error || e?.message || 'Commit fehlgeschlagen'
  } finally {
    committing.value = false
  }
}

// Socket.IO for real-time commit updates
let socket = null
let subscribedPromptId = null
let onSocketConnect = null

function handleCommitCreated(payload) {
  if (!payload || payload.prompt_id !== props.promptId) return
  loadCommits(true)
  emit('committed')
}

function setupCommitSocket(promptId) {
  if (!promptId) return
  socket = getSocket()
  if (!socket) return

  socket.on('prompt:commit_created', handleCommitCreated)

  onSocketConnect = () => {
    socket.emit('prompt:subscribe', { prompt_id: promptId })
  }

  if (socket.connected) {
    onSocketConnect()
  }
  socket.on('connect', onSocketConnect)
  subscribedPromptId = promptId
}

function cleanupCommitSocket() {
  if (!socket) return
  socket.off('prompt:commit_created', handleCommitCreated)
  if (onSocketConnect) socket.off('connect', onSocketConnect)
  if (subscribedPromptId) {
    socket.emit('prompt:unsubscribe', { prompt_id: subscribedPromptId })
  }
  subscribedPromptId = null
  onSocketConnect = null
}

watch(
  () => props.promptId,
  async (nextId, prevId) => {
    if (prevId && prevId !== nextId) {
      cleanupCommitSocket()
    }
    commits.value = []
    commitMessage.value = ''
    await loadCommits(true)
    if (nextId) {
      setupCommitSocket(nextId)
    }
  }
)

onMounted(async () => {
  await loadCommits()
  if (props.promptId) {
    setupCommitSocket(props.promptId)
  }
})

onUnmounted(() => {
  cleanupCommitSocket()
})
</script>

<style scoped>
/* LLARS Design Variables */
.git-panel-wrapper {
  --llars-primary: #b0ca97;
  --llars-accent: #88c4c8;
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

.change-indicator {
  font-family: monospace;
  font-size: 11px;
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

/* Commit Section */
.commit-section {
  display: flex;
  flex-direction: column;
}

.user-changes {
  margin-bottom: 12px;
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

.commit-input :deep(.v-field) {
  border-radius: var(--llars-radius-sm) !important;
}

.commit-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

/* History Section */
.history-section {
  display: flex;
  flex-direction: column;
}

.history-list {
  max-height: 200px;
  overflow-y: auto;
}

.empty-history {
  color: rgb(var(--v-theme-on-surface-variant));
  font-size: 13px;
  text-align: center;
  padding: 20px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--llars-radius-sm);
  transition: background 0.15s;
}

.history-item:hover {
  background: rgba(var(--v-theme-primary), 0.08);
}

.commit-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--llars-primary);
  flex-shrink: 0;
}

.commit-info {
  flex: 1;
  min-width: 0;
}

.commit-message {
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

.commit-meta {
  font-size: 11px;
  color: rgb(var(--v-theme-on-surface-variant));
  display: block;
}

.more-commits {
  text-align: center;
  padding: 8px;
  font-size: 12px;
  color: var(--llars-primary);
  font-weight: 500;
}

/* Responsive */
@media (max-width: 600px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}
</style>
