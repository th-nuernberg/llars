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
          v-if="changedFiles.length > 0"
          variant="warning"
          size="small"
        >
          {{ changedFiles.length }} {{ changedFiles.length === 1 ? 'Datei' : 'Dateien' }}
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
          v-if="changedFiles.length > 0"
          variant="warning"
          size="small"
        >
          {{ changedFiles.length }} geändert
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
            title="Änderungen prüfen"
            :loading="checkingChanges"
            @click="checkForChanges"
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

        <!-- Two columns: Files + Commit -->
        <div class="content-grid">
          <!-- Left: Changed Files -->
          <div class="files-section">
            <div class="section-title">
              <v-icon size="16" class="mr-1">mdi-file-document-multiple</v-icon>
              Geänderte Dateien
              <v-spacer />
              <span v-if="changedFiles.length > 0" class="file-count">
                {{ selectedFiles.length }}/{{ changedFiles.length }}
              </span>
            </div>

            <v-skeleton-loader v-if="checkingChanges" type="list-item@3" />
            <div v-else-if="changedFiles.length === 0" class="empty-files">
              Keine Änderungen
            </div>
            <div v-else class="file-list">
              <!-- Select All -->
              <div class="select-all-row">
                <v-checkbox
                  v-model="allSelected"
                  density="compact"
                  hide-details
                  :indeterminate="someSelected && !allSelected"
                  @update:model-value="toggleSelectAll"
                >
                  <template #label>
                    <span class="select-all-label">Alle auswählen</span>
                  </template>
                </v-checkbox>
              </div>

              <!-- File list -->
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
                <v-icon size="16" class="file-icon">mdi-file-document-outline</v-icon>
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
                      <v-icon size="14">mdi-undo</v-icon>
                    </v-btn>
                  </template>
                  <span>Änderungen verwerfen</span>
                </v-tooltip>
              </div>
            </div>
          </div>

          <!-- Right: Commit Section -->
          <div class="commit-section">
            <div class="section-title">
              <v-icon size="16" class="mr-1">mdi-pencil-plus</v-icon>
              Commit
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
                title="Ausgewählte Dateien committen"
                @click="submitCommit"
              >
                Commit ({{ selectedFiles.length }})
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
            <v-icon size="24" color="white">mdi-source-branch</v-icon>
          </div>
          <span class="header-title">Workspace Commit</span>
          <LTag
            v-if="changedFiles.length > 0"
            variant="warning"
            size="small"
          >
            {{ changedFiles.length }} geänderte Dateien
          </LTag>
          <v-spacer />
          <LBtn
            variant="text"
            size="small"
            prepend-icon="mdi-refresh"
            :loading="checkingChanges"
            title="Änderungen prüfen"
            @click="checkForChanges"
          >
            Aktualisieren
          </LBtn>
          <LBtn
            variant="cancel"
            size="small"
            prepend-icon="mdi-fullscreen-exit"
            class="ml-2"
            title="Vollbild schließen"
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
            <!-- Left Column: Changed Files -->
            <div class="fullscreen-left">
              <div class="git-card">
                <div class="card-header">
                  <v-icon size="18" class="mr-2">mdi-file-document-multiple</v-icon>
                  Geänderte Dateien
                  <v-spacer />
                  <span class="file-count-header">{{ selectedFiles.length }}/{{ changedFiles.length }}</span>
                </div>
                <div class="card-content">
                  <v-skeleton-loader v-if="checkingChanges" type="list-item@6" />
                  <div v-else-if="changedFiles.length === 0" class="empty-state">
                    <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-check-circle</v-icon>
                    <span>Keine uncommitted Änderungen</span>
                  </div>
                  <div v-else>
                    <!-- Select All / None buttons -->
                    <div class="bulk-actions">
                      <LBtn variant="text" size="small" @click="selectAll">
                        Alle auswählen
                      </LBtn>
                      <LBtn variant="text" size="small" @click="deselectAll">
                        Keine auswählen
                      </LBtn>
                    </div>

                    <v-divider class="my-2" />

                    <!-- File list -->
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
                        <v-icon size="20" class="file-icon" :color="getFileIconColor(file.path)">
                          {{ getFileIcon(file.path) }}
                        </v-icon>
                        <div class="file-details">
                          <div class="file-path-full">{{ file.path }}</div>
                          <div class="file-stats-full">
                            <span class="stat-badge success">+{{ file.insertions }}</span>
                            <span class="stat-badge error">-{{ file.deletions }}</span>
                            <span v-if="!file.has_baseline" class="new-badge">NEU</span>
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
                              <v-icon size="18">mdi-undo</v-icon>
                            </v-btn>
                          </template>
                          <span>Änderungen verwerfen</span>
                        </v-tooltip>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Right Column: Commit -->
            <div class="fullscreen-right">
              <div class="git-card">
                <div class="card-header">
                  <v-icon size="18" class="mr-2">mdi-pencil-plus</v-icon>
                  Commit erstellen
                </div>
                <div class="card-content">
                  <!-- Summary -->
                  <div v-if="selectedFiles.length > 0" class="commit-summary">
                    <div class="summary-item">
                      <v-icon size="16" color="primary">mdi-file-check</v-icon>
                      <span>{{ selectedFiles.length }} {{ selectedFiles.length === 1 ? 'Datei' : 'Dateien' }} ausgewählt</span>
                    </div>
                    <div class="summary-item">
                      <v-icon size="16" color="success">mdi-plus</v-icon>
                      <span>{{ totalInsertions }} Zeilen hinzugefügt</span>
                    </div>
                    <div class="summary-item">
                      <v-icon size="16" color="error">mdi-minus</v-icon>
                      <span>{{ totalDeletions }} Zeilen entfernt</span>
                    </div>
                  </div>
                  <div v-else class="no-selection">
                    <v-icon size="32" color="grey-lighten-1" class="mb-2">mdi-checkbox-blank-off-outline</v-icon>
                    <span>Keine Dateien ausgewählt</span>
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
                    rows="4"
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
                      title="Ausgewählte Dateien committen"
                      @click="submitCommit"
                    >
                      {{ selectedFiles.length }} {{ selectedFiles.length === 1 ? 'Datei' : 'Dateien' }} committen
                    </LBtn>
                  </div>
                </div>
              </div>

              <!-- Recent Commits -->
              <div class="git-card mt-4">
                <div class="card-header">
                  <v-icon size="18" class="mr-2">mdi-history</v-icon>
                  Letzte Commits
                </div>
                <div class="card-content history-content">
                  <v-skeleton-loader v-if="loadingCommits" type="list-item@4" />
                  <div v-else-if="recentCommits.length === 0" class="empty-state small">
                    <span>Noch keine Commits</span>
                  </div>
                  <div v-else class="history-list-full">
                    <div
                      v-for="c in recentCommits"
                      :key="c.id"
                      class="history-item-full"
                    >
                      <div class="commit-indicator" />
                      <div class="commit-details">
                        <div class="commit-message-full">{{ c.message }}</div>
                        <div class="commit-meta-full">
                          <span class="author">{{ c.author_username }}</span>
                          <span class="date">{{ formatDate(c.created_at) }}</span>
                          <span class="files-count">{{ c.file_count || 1 }} Datei(en)</span>
                        </div>
                      </div>
                    </div>
                  </div>
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
          <v-icon color="warning">mdi-alert-circle</v-icon>
          Änderungen verwerfen?
        </v-card-title>
        <v-card-text>
          <p>
            Alle nicht committeten Änderungen in
            <strong>{{ rollbackTarget?.path }}</strong>
            werden unwiderruflich verworfen.
          </p>
          <p class="text-medium-emphasis mt-2 mb-0">
            Die Datei wird auf den letzten Commit zurückgesetzt.
          </p>
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer />
          <LBtn variant="cancel" @click="cancelRollback">
            Abbrechen
          </LBtn>
          <LBtn variant="danger" prepend-icon="mdi-undo" @click="executeRollback">
            Verwerfen
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import axios from 'axios'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'
import { getSocket } from '@/services/socketService'

const props = defineProps({
  workspaceId: { type: Number, required: true },
  canCommit: { type: Boolean, default: false },
  apiPrefix: { type: String, default: '/api/latex-collab' }
})

const emit = defineEmits(['committed', 'rollback'])

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080'

const expanded = ref(false)
const fullscreen = ref(false)

// Changed files state
const changedFiles = ref([])
const selectedFiles = ref([])
const checkingChanges = ref(false)
const loadError = ref('')

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

    if (diffMins < 1) return 'Gerade eben'
    if (diffMins < 60) return `vor ${diffMins} Min.`
    if (diffHours < 24) return `vor ${diffHours} Std.`
    if (diffDays < 7) return `vor ${diffDays} Tagen`
    return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: '2-digit' })
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
  showRollbackConfirm.value = true
}

function cancelRollback() {
  rollbackTarget.value = null
  showRollbackConfirm.value = false
}

async function executeRollback() {
  if (!rollbackTarget.value) return

  const file = rollbackTarget.value
  rollingBack.value = file.id
  showRollbackConfirm.value = false

  try {
    await axios.post(
      `${API_BASE}${props.apiPrefix}/documents/${file.id}/rollback`,
      {},
      { headers: authHeaders() }
    )

    // Emit rollback event so parent can refresh the editor
    emit('rollback', file.id)

    // Refresh changes list
    await checkForChanges()
  } catch (e) {
    commitError.value = e?.response?.data?.error || e?.message || 'Rollback fehlgeschlagen'
  } finally {
    rollingBack.value = null
    rollbackTarget.value = null
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

    // Auto-select all changed files
    selectedFiles.value = changedFiles.value.map(f => f.id)
  } catch (e) {
    loadError.value = e?.response?.data?.error || e?.message || 'Fehler beim Prüfen der Änderungen'
    changedFiles.value = []
    selectedFiles.value = []
  } finally {
    checkingChanges.value = false
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
    commitError.value = e?.response?.data?.error || e?.message || 'Commit fehlgeschlagen'
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

  if (newId) {
    await Promise.all([checkForChanges(), loadRecentCommits()])
    setupSocket()
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
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  min-height: calc(100vh - 140px);
}

.fullscreen-left,
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

/* Responsive */
@media (max-width: 1200px) {
  .fullscreen-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}
</style>
