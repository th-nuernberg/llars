<template>
  <v-card class="git-root" variant="outlined">
    <v-card-title class="d-flex align-center">
      <v-icon class="mr-2" color="primary">mdi-source-branch</v-icon>
      Git Panel
      <v-spacer />
      <v-chip size="small" variant="tonal" :color="summary?.hasChanges ? 'warning' : 'info'">
        <template v-if="summary?.insertions !== undefined">
          +{{ summary?.insertions || 0 }} / -{{ summary?.deletions || 0 }}
        </template>
        <template v-else>
          {{ summary?.totalChangedLines || 0 }} Änderungen
        </template>
      </v-chip>
      <v-btn icon="mdi-refresh" variant="text" class="ml-1" title="History neu laden" @click="loadCommits(true)" />
      <v-btn
        icon
        variant="text"
        class="ml-1"
        :title="expanded ? 'Einklappen' : 'Ausklappen'"
        @click="expanded = !expanded"
      >
        <v-icon>{{ expanded ? 'mdi-chevron-down' : 'mdi-chevron-up' }}</v-icon>
      </v-btn>
    </v-card-title>

    <v-divider />

    <v-expand-transition>
      <div v-show="expanded">
        <v-card-text>
          <v-alert v-if="loadError" type="error" variant="tonal" class="mb-4">
            {{ loadError }}
          </v-alert>
          <v-row>
            <v-col cols="12" md="5">
              <div class="text-subtitle-2 mb-2">Uncommitted Changes</div>
              <div v-if="!summary?.hasChanges && (summary?.users || []).length === 0" class="text-body-2 text-medium-emphasis">
                Keine uncommitted Änderungen.
              </div>
              <div v-else class="mb-3">
                <div v-if="summary?.insertions !== undefined" class="text-body-2 mb-2">
                  <span class="text-success">+{{ summary?.insertions || 0 }} Zeichen eingefügt</span>
                  <span class="mx-2">|</span>
                  <span class="text-error">-{{ summary?.deletions || 0 }} Zeichen gelöscht</span>
                </div>
                <v-list v-if="(summary?.users || []).length > 0" density="compact" class="pa-0">
                  <v-list-item
                    v-for="u in summary.users"
                    :key="u.username"
                    class="px-0"
                  >
                    <template #prepend>
                      <span class="user-dot" :style="{ backgroundColor: u.color }" />
                    </template>
                    <v-list-item-title class="text-body-2">
                      {{ u.username }}
                    </v-list-item-title>
                    <v-list-item-subtitle class="text-caption">
                      {{ u.changedLines }} Zeilen
                    </v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </div>

              <v-divider class="my-4" />

              <div class="text-subtitle-2 mb-2">Commit</div>
              <v-alert v-if="commitError" type="error" variant="tonal" class="mb-3">
                {{ commitError }}
              </v-alert>
              <v-text-field
                v-model="commitMessage"
                label="Commit Message"
                variant="outlined"
                density="comfortable"
                :disabled="!canCommit"
                :hint="canCommit ? 'Pflichtfeld' : 'Du hast keine Edit-Rechte'"
                persistent-hint
              />
              <div class="d-flex justify-end">
                <v-btn
                  color="primary"
                  :loading="committing"
                  :disabled="!canSubmitCommit"
                  @click="submitCommit"
                >
                  Commit
                </v-btn>
              </div>
            </v-col>

            <v-col cols="12" md="7">
              <div class="text-subtitle-2 mb-2">History</div>
              <v-skeleton-loader v-if="isLoading('commits')" type="list-item@6" />
              <v-alert
                v-else-if="commits.length === 0"
                type="info"
                variant="tonal"
              >
                Noch keine Commits.
              </v-alert>
              <v-list v-else density="compact" class="history-list">
                <v-list-item
                  v-for="c in commits"
                  :key="c.id"
                  :active="c.id === compareCommitId"
                  active-class="history-item--active"
                  @click="selectCommit(c.id)"
                >
                  <v-list-item-title class="text-body-2">
                    {{ c.message }}
                  </v-list-item-title>
                  <v-list-item-subtitle class="text-caption">
                    {{ c.author_username }} · {{ formatDate(c.created_at) }}
                  </v-list-item-subtitle>
                  <template #append>
                    <v-chip size="x-small" variant="tonal">#{{ c.id }}</v-chip>
                  </template>
                </v-list-item>
              </v-list>
            </v-col>

            <v-col cols="12">
              <v-divider class="my-3" />
              <div class="d-flex flex-wrap align-center ga-3 mb-2">
                <div class="text-subtitle-2">Diff</div>
                <v-select
                  v-model="compareMode"
                  :items="compareModeOptions"
                  label="Modus"
                  density="compact"
                  variant="outlined"
                  hide-details
                  class="diff-select"
                />
                <v-select
                  v-if="compareMode === 'commit-range'"
                  v-model="baseCommitId"
                  :items="baseCommitOptions"
                  :disabled="baseCommitOptions.length === 0"
                  label="Basis"
                  density="compact"
                  variant="outlined"
                  hide-details
                  class="diff-select"
                />
                <v-select
                  v-if="compareMode === 'commit-range'"
                  v-model="compareCommitId"
                  :items="commitOptions"
                  :disabled="commitOptions.length === 0"
                  label="Vergleich"
                  density="compact"
                  variant="outlined"
                  hide-details
                  class="diff-select"
                />
                <v-btn
                  icon="mdi-refresh"
                  variant="text"
                  class="ml-auto"
                  title="Diff neu laden"
                  @click="refreshDiff(true)"
                />
              </div>

              <v-alert v-if="diffError" type="error" variant="tonal" class="mb-3">
                {{ diffError }}
              </v-alert>

              <v-skeleton-loader v-if="isLoading('diff')" type="table" height="240" />
              <MarkdownDiffViewer
                v-else
                :base-text="diffBaseText"
                :compare-text="diffCompareText"
                :base-label="diffBaseLabel"
                :compare-label="diffCompareLabel"
              />
            </v-col>
          </v-row>
        </v-card-text>
      </div>
    </v-expand-transition>
  </v-card>
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
  // Function to get current content from editor for commit snapshot
  getContent: { type: Function, default: null }
})

const emit = defineEmits(['committed'])

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080'
const { isLoading, withLoading } = useSkeletonLoading(['commits', 'diff'])

const expanded = ref(true)
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

const compareModeOptions = [
  { title: 'Working tree vs letzter Commit', value: 'working' },
  { title: 'Commit vs Commit', value: 'commit-range' }
]

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
    return new Date(iso).toLocaleString()
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
    `${API_BASE}/api/markdown-collab/documents/${props.documentId}/baseline`,
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
    `${API_BASE}/api/markdown-collab/documents/${props.documentId}/commits/${commitId}`,
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

  socket.on('markdown_collab:commit_created', handleCommitCreated)

  onSocketConnect = () => {
    socket.emit('markdown_collab:subscribe_document', { document_id: documentId })
  }

  if (socket.connected) {
    onSocketConnect()
  }
  socket.on('connect', onSocketConnect)
  subscribedDocId = documentId
}

function cleanupCommitSocket() {
  if (!socket) return
  socket.off('markdown_collab:commit_created', handleCommitCreated)
  if (onSocketConnect) socket.off('connect', onSocketConnect)
  if (subscribedDocId) {
    socket.emit('markdown_collab:unsubscribe_document', { document_id: subscribedDocId })
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
      const res = await axios.get(`${API_BASE}/api/markdown-collab/documents/${props.documentId}/commits`, {
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
  // Use hasChanges from summary (based on actual diff comparison with baseline)
  const hasChanges = props.summary?.hasChanges === true || (props.summary?.totalChangedLines || 0) > 0
  return props.canCommit && msgOk && hasChanges
})

async function submitCommit() {
  if (!canSubmitCommit.value) return
  committing.value = true
  commitError.value = ''
  try {
    // Get current content for snapshot (required for character-level diff)
    const contentSnapshot = props.getContent ? props.getContent() : null

    await axios.post(
      `${API_BASE}/api/markdown-collab/documents/${props.documentId}/commit`,
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
.git-root {
  background: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
  border-top-left-radius: 0;
  border-top-right-radius: 0;
}

.user-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  display: inline-block;
  margin-right: 10px;
}

.history-list {
  max-height: 220px;
  overflow: auto;
}

.history-item--active {
  background: rgba(var(--v-theme-primary), 0.12);
}

.diff-select {
  min-width: 220px;
  max-width: 360px;
}
</style>
