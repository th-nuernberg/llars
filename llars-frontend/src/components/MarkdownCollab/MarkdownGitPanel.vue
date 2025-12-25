<template>
  <div class="git-panel-wrapper">
    <!-- Collapsed State: Thin bar -->
    <div v-if="!expanded && !fullscreen" class="git-panel-collapsed" @click="expanded = true">
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
    <div v-if="expanded && !fullscreen" class="git-panel-expanded">
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
            title="Vollbild"
            @click="fullscreen = true"
          >
            <v-icon size="18">mdi-fullscreen</v-icon>
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
              History
            </div>

            <v-skeleton-loader v-if="isLoading('commits')" type="list-item@4" />
            <div v-else-if="commits.length === 0" class="empty-history">
              Noch keine Commits
            </div>
            <div v-else class="history-list">
              <div
                v-for="c in commits.slice(0, 5)"
                :key="c.id"
                class="history-item"
                :class="{ active: c.id === compareCommitId }"
                @click="selectCommit(c.id)"
              >
                <div class="commit-info">
                  <span class="commit-message">{{ c.message }}</span>
                  <span class="commit-meta">{{ c.author_username }} · {{ formatDate(c.created_at) }}</span>
                </div>
                <LTag variant="gray" size="small">#{{ c.id }}</LTag>
              </div>
              <div v-if="commits.length > 5" class="more-commits" @click="fullscreen = true">
                +{{ commits.length - 5 }} weitere...
              </div>
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
            <v-icon size="24" color="white">mdi-source-branch</v-icon>
          </div>
          <span class="header-title">Git Panel</span>
          <LTag
            v-if="summary?.hasChanges"
            variant="warning"
            size="small"
          >
            +{{ summary?.insertions || 0 }} / -{{ summary?.deletions || 0 }}
          </LTag>
          <v-spacer />
          <LBtn
            variant="text"
            size="small"
            prepend-icon="mdi-refresh"
            @click="loadCommits(true)"
          >
            Aktualisieren
          </LBtn>
          <LBtn
            variant="cancel"
            size="small"
            prepend-icon="mdi-fullscreen-exit"
            class="ml-2"
            @click="fullscreen = false"
          >
            Schließen
          </LBtn>
        </div>

        <!-- Fullscreen Content -->
        <div class="fullscreen-content">
          <v-alert v-if="loadError" type="error" variant="tonal" class="mb-4">
            {{ loadError }}
          </v-alert>

          <div class="fullscreen-grid">
            <!-- Left Column: Commit + Changes -->
            <div class="fullscreen-left">
              <!-- Commit Card -->
              <div class="git-card">
                <div class="card-header">
                  <v-icon size="18" class="mr-2">mdi-pencil-plus</v-icon>
                  Neuer Commit
                </div>
                <div class="card-content">
                  <!-- Change Stats -->
                  <div v-if="summary?.hasChanges" class="change-stats">
                    <div class="stat-item success">
                      <v-icon size="16">mdi-plus</v-icon>
                      <span>{{ summary?.insertions || 0 }} eingefügt</span>
                    </div>
                    <div class="stat-item error">
                      <v-icon size="16">mdi-minus</v-icon>
                      <span>{{ summary?.deletions || 0 }} gelöscht</span>
                    </div>
                  </div>
                  <div v-else class="no-changes">
                    <v-icon size="32" color="success" class="mb-2">mdi-check-circle</v-icon>
                    <span>Keine uncommitted Änderungen</span>
                  </div>

                  <!-- User contributions -->
                  <div v-if="(summary?.users || []).length > 0" class="user-contributions">
                    <div class="contributions-title">Beiträge</div>
                    <div
                      v-for="u in summary.users"
                      :key="u.username"
                      class="contribution-item"
                    >
                      <span class="user-dot large" :style="{ backgroundColor: u.color }" />
                      <span class="user-name">{{ u.username }}</span>
                      <span class="user-lines">{{ u.changedLines }} Zeilen</span>
                    </div>
                  </div>

                  <v-divider class="my-4" />

                  <v-alert v-if="commitError" type="error" variant="tonal" class="mb-3">
                    {{ commitError }}
                  </v-alert>

                  <v-textarea
                    v-model="commitMessage"
                    placeholder="Beschreibe deine Änderungen..."
                    variant="outlined"
                    density="comfortable"
                    :disabled="!canCommit"
                    rows="3"
                    hide-details
                    class="commit-textarea"
                  />

                  <div class="commit-actions mt-3">
                    <LBtn
                      variant="primary"
                      :loading="committing"
                      :disabled="!canSubmitCommit"
                      prepend-icon="mdi-check"
                      block
                      @click="submitCommit"
                    >
                      Änderungen committen
                    </LBtn>
                  </div>
                </div>
              </div>
            </div>

            <!-- Middle Column: History -->
            <div class="fullscreen-middle">
              <div class="git-card">
                <div class="card-header">
                  <v-icon size="18" class="mr-2">mdi-history</v-icon>
                  Commit History
                  <v-spacer />
                  <span class="commit-count">{{ commits.length }} Commits</span>
                </div>
                <div class="card-content history-content">
                  <v-skeleton-loader v-if="isLoading('commits')" type="list-item@8" />
                  <div v-else-if="commits.length === 0" class="empty-state">
                    <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-source-commit</v-icon>
                    <span>Noch keine Commits vorhanden</span>
                  </div>
                  <div v-else class="history-list-full">
                    <div
                      v-for="c in commits"
                      :key="c.id"
                      class="history-item-full"
                      :class="{ active: c.id === compareCommitId }"
                      @click="selectCommit(c.id)"
                    >
                      <div class="commit-indicator" />
                      <div class="commit-details">
                        <div class="commit-message-full">{{ c.message }}</div>
                        <div class="commit-meta-full">
                          <span class="author">{{ c.author_username }}</span>
                          <span class="date">{{ formatDate(c.created_at) }}</span>
                        </div>
                      </div>
                      <LTag variant="gray" size="small">#{{ c.id }}</LTag>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Right Column: Diff -->
            <div class="fullscreen-right">
              <div class="git-card">
                <div class="card-header">
                  <v-icon size="18" class="mr-2">mdi-file-compare</v-icon>
                  Diff Ansicht
                  <v-spacer />
                  <v-btn-toggle
                    v-model="compareMode"
                    density="compact"
                    variant="outlined"
                    divided
                    mandatory
                    class="mode-toggle"
                  >
                    <v-btn value="working" size="small">Working</v-btn>
                    <v-btn value="commit-range" size="small">Commits</v-btn>
                  </v-btn-toggle>
                </div>
                <div class="card-content diff-content">
                  <!-- Commit range selectors -->
                  <div v-if="compareMode === 'commit-range'" class="diff-selectors">
                    <v-select
                      v-model="baseCommitId"
                      :items="baseCommitOptions"
                      label="Basis"
                      density="compact"
                      variant="outlined"
                      hide-details
                    />
                    <v-icon class="mx-2">mdi-arrow-right</v-icon>
                    <v-select
                      v-model="compareCommitId"
                      :items="commitOptions"
                      label="Vergleich"
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
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import axios from 'axios'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import MarkdownDiffViewer from '@/components/MarkdownCollab/MarkdownDiffViewer.vue'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'
import { getSocket } from '@/services/socketService'

const props = defineProps({
  documentId: { type: Number, required: true },
  summary: { type: Object, default: () => ({ users: [], totalChangedLines: 0, hasChanges: false }) },
  canCommit: { type: Boolean, default: false },
  getContent: { type: Function, default: null },
  apiPrefix: { type: String, default: '/api/markdown-collab' },
  socketNamespace: { type: String, default: 'markdown_collab' }
})

const emit = defineEmits(['committed'])

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080'
const { isLoading, withLoading } = useSkeletonLoading(['commits', 'diff'])

const expanded = ref(false)
const fullscreen = ref(false)
const commits = ref([])
const compareMode = ref('working')
const baseCommitId = ref(null)
const compareCommitId = ref(null)

const commitMessage = ref('')
const committing = ref(false)
const commitError = ref('')
const loadError = ref('')
const diffError = ref('')

const diffBaseText = ref('')
const diffCompareText = ref('')
const diffBaseLabel = ref('')
const diffCompareLabel = ref('')

const baselineSnapshot = ref('')
const baselineCommitId = ref(null)
const baselineCommitMessage = ref('')

const commitSnapshotCache = new Map()
let workingSyncTimer = null

const commitOptions = computed(() => commits.value.map((c) => ({
  title: `#${c.id} · ${c.message}`,
  value: c.id
})))

const INITIAL_BASE = '__initial__'

const baseCommitOptions = computed(() => [
  { title: 'Initial (kein Commit)', value: INITIAL_BASE },
  ...commitOptions.value
])

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

function getCommitById(commitId) {
  return commits.value.find((c) => c.id === commitId) || null
}

function formatCommitLabel(commit) {
  if (!commit) return '—'
  const message = commit.message ? String(commit.message).trim() : ''
  return `#${commit.id}${message ? ` · ${message}` : ''}`
}

async function loadBaselineSnapshot(force = false) {
  if (!props.documentId) return
  if (!force && baselineCommitId.value !== null) return

  const res = await axios.get(
    `${API_BASE}${props.apiPrefix}/documents/${props.documentId}/baseline`,
    { headers: authHeaders() }
  )
  baselineSnapshot.value = res.data?.baseline || ''
  baselineCommitId.value = res.data?.commit_id ?? null
  baselineCommitMessage.value = res.data?.commit_message || ''
}

async function fetchCommitSnapshot(commitId) {
  if (!commitId || commitId === INITIAL_BASE) return ''
  if (commitSnapshotCache.has(commitId)) {
    return commitSnapshotCache.get(commitId) || ''
  }
  const res = await axios.get(
    `${API_BASE}${props.apiPrefix}/documents/${props.documentId}/commits/${commitId}`,
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
  await withLoading('diff', async () => {
    diffError.value = ''
    try {
      if (compareMode.value === 'working') {
        await loadBaselineSnapshot(force)
        diffBaseText.value = baselineSnapshot.value || ''
        diffCompareText.value = props.getContent ? String(props.getContent() || '') : ''
        diffBaseLabel.value = baselineCommitId.value
          ? `#${baselineCommitId.value}${baselineCommitMessage.value ? ` · ${baselineCommitMessage.value}` : ''}`
          : 'Initial (kein Commit)'
        diffCompareLabel.value = 'Working tree'
        return
      }

      const compareCommit = getCommitById(compareCommitId.value)
      if (!compareCommit) {
        diffBaseText.value = ''
        diffCompareText.value = ''
        diffBaseLabel.value = '—'
        diffCompareLabel.value = '—'
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
        : 'Initial (kein Commit)'
      diffCompareLabel.value = formatCommitLabel(compareCommit)
    } catch (e) {
      diffBaseText.value = ''
      diffCompareText.value = ''
      diffBaseLabel.value = '—'
      diffCompareLabel.value = '—'
      diffError.value = e?.response?.data?.error || e?.message || 'Diff konnte nicht geladen werden'
    }
  })
}

function selectCommit(commitId) {
  if (!commitId) return
  compareCommitId.value = commitId
  compareMode.value = 'commit-range'
  if (!baseCommitId.value || baseCommitId.value === commitId) {
    const selectedIndex = commits.value.findIndex((c) => c.id === commitId)
    const previous = selectedIndex >= 0 ? commits.value[selectedIndex + 1] : null
    baseCommitId.value = previous ? previous.id : INITIAL_BASE
  }
}

let socket = null
let subscribedDocId = null
let onSocketConnect = null

function handleCommitCreated(payload) {
  if (!payload || payload.document_id !== props.documentId) return
  commitSnapshotCache.clear()
  baselineCommitId.value = null
  loadCommits(true)
  emit('committed')
}

function setupCommitSocket(documentId) {
  if (!documentId) return
  socket = getSocket()
  if (!socket) return

  socket.on(`${props.socketNamespace}:commit_created`, handleCommitCreated)

  onSocketConnect = () => {
    socket.emit(`${props.socketNamespace}:subscribe_document`, { document_id: documentId })
  }

  if (socket.connected) {
    onSocketConnect()
  }
  socket.on('connect', onSocketConnect)
  subscribedDocId = documentId
}

function cleanupCommitSocket() {
  if (!socket) return
  socket.off(`${props.socketNamespace}:commit_created`, handleCommitCreated)
  if (onSocketConnect) socket.off('connect', onSocketConnect)
  if (subscribedDocId) {
    socket.emit(`${props.socketNamespace}:unsubscribe_document`, { document_id: subscribedDocId })
  }
  subscribedDocId = null
  onSocketConnect = null
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

async function loadCommits(force = false) {
  await withLoading('commits', async () => {
    loadError.value = ''
    try {
      const res = await axios.get(`${API_BASE}${props.apiPrefix}/documents/${props.documentId}/commits`, {
        headers: authHeaders(),
        params: force ? { _ts: Date.now() } : undefined
      })
      commits.value = res.data.commits || []
      if (commits.value.length > 0) {
        const compareExists = commits.value.some((c) => c.id === compareCommitId.value)
        if (!compareExists) {
          compareCommitId.value = commits.value[0].id
        }
        const baseExists = commits.value.some((c) => c.id === baseCommitId.value)
        if (!baseExists) {
          baseCommitId.value = commits.value[1]?.id || INITIAL_BASE
        }
      } else {
        compareCommitId.value = null
        baseCommitId.value = INITIAL_BASE
      }
    } catch (e) {
      commits.value = []
      compareCommitId.value = null
      baseCommitId.value = INITIAL_BASE
      loadError.value = e?.response?.data?.error || e?.message || 'History konnte nicht geladen werden'
    }
  })
  await refreshDiff(force)
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
      `${API_BASE}${props.apiPrefix}/documents/${props.documentId}/commit`,
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

watch(
  () => props.summary,
  () => {
    syncWorkingDiffText()
  },
  { deep: true }
)

watch(
  compareMode,
  async () => {
    await refreshDiff(false)
  }
)

watch(
  [baseCommitId, compareCommitId],
  async () => {
    if (compareMode.value === 'commit-range') {
      await refreshDiff(false)
    }
  }
)

watch(
  () => props.documentId,
  async (nextId, prevId) => {
    if (prevId && prevId !== nextId) {
      cleanupCommitSocket()
    }
    resetDiffState()
    commitMessage.value = ''
    commits.value = []
    await loadCommits(true)
    if (nextId) {
      setupCommitSocket(nextId)
    }
  }
)

onMounted(async () => {
  await loadCommits()
  if (props.documentId) {
    setupCommitSocket(props.documentId)
  }
})

onUnmounted(() => {
  cleanupCommitSocket()
  resetDiffState()
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

.user-dot.large {
  width: 12px;
  height: 12px;
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
  max-height: 180px;
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
  cursor: pointer;
  transition: background 0.15s;
}

.history-item:hover {
  background: rgba(var(--v-theme-primary), 0.08);
}

.history-item.active {
  background: rgba(var(--v-theme-primary), 0.15);
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
}

.commit-meta {
  font-size: 11px;
  color: rgb(var(--v-theme-on-surface-variant));
}

.more-commits {
  text-align: center;
  padding: 8px;
  font-size: 12px;
  color: var(--llars-primary);
  cursor: pointer;
  font-weight: 500;
}

.more-commits:hover {
  text-decoration: underline;
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
  height: 100%;
}

.card-header {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  font-weight: 600;
  font-size: 14px;
  display: flex;
  align-items: center;
}

.commit-count {
  font-weight: 400;
  font-size: 12px;
  color: rgb(var(--v-theme-on-surface-variant));
}

.card-content {
  padding: 16px;
  flex: 1;
  overflow-y: auto;
}

/* Change Stats */
.change-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: var(--llars-radius-sm);
  font-size: 13px;
  font-weight: 500;
}

.stat-item.success {
  background: rgba(152, 212, 187, 0.2);
  color: #2e7d32;
}

.stat-item.error {
  background: rgba(232, 160, 135, 0.2);
  color: #c62828;
}

.no-changes {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px;
  color: rgb(var(--v-theme-on-surface-variant));
  font-size: 13px;
}

/* User Contributions */
.user-contributions {
  margin-bottom: 16px;
}

.contributions-title {
  font-size: 12px;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface-variant));
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.contribution-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
}

.commit-textarea :deep(.v-field) {
  border-radius: var(--llars-radius-sm) !important;
}

/* History Full */
.history-content {
  padding: 8px !important;
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
  cursor: pointer;
  transition: background 0.15s;
}

.history-item-full:hover {
  background: rgba(var(--v-theme-primary), 0.08);
}

.history-item-full.active {
  background: rgba(var(--v-theme-primary), 0.15);
}

.commit-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--llars-primary);
  flex-shrink: 0;
}

.history-item-full.active .commit-indicator {
  background: var(--llars-accent);
  box-shadow: 0 0 0 3px rgba(136, 196, 200, 0.3);
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

.mode-toggle {
  border-radius: var(--llars-radius-sm) !important;
}

.mode-toggle .v-btn {
  font-size: 11px !important;
  text-transform: none !important;
}

.diff-viewer-full {
  flex: 1;
  min-height: 0;
}

/* Responsive */
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
</style>
