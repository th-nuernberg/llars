<template>
  <v-container fluid class="pa-0 workspace-root">
    <v-row no-gutters class="h-100">
      <!-- Left: Tree -->
      <v-col cols="3" class="tree-col">
        <MarkdownTreePanel
          :workspace-id="workspaceId"
          :nodes="treeNodes"
          :selected-id="selectedNodeId"
          :loading="isLoading('tree')"
          :can-edit="hasPermission('feature:markdown_collab:edit')"
          @select="handleSelectNode"
          @create="handleCreateNode"
          @rename="handleRenameNode"
          @remove="handleDeleteNode"
          @move="handleMoveNode"
        />
      </v-col>

      <!-- Right: Editor/Preview -->
      <v-col cols="9" class="content-col">
        <div class="content-header">
          <div class="d-flex align-center">
            <v-icon class="mr-2" color="primary">mdi-language-markdown</v-icon>
            <div>
              <div class="text-subtitle-1 font-weight-medium">
                {{ selectedNode?.title || 'Kein Dokument ausgewählt' }}
              </div>
              <div class="text-caption text-medium-emphasis">
                Workspace: {{ workspace?.name || `#${workspaceId}` }}
              </div>
            </div>
          </div>

          <v-spacer />

          <v-btn
            v-if="canShareWorkspace"
            icon="mdi-account-multiple-plus"
            variant="text"
            title="Workspace teilen"
            @click="openShareDialog"
          />

          <v-btn-toggle
            v-model="viewMode"
            mandatory
            density="comfortable"
            variant="outlined"
            class="mode-toggle"
          >
            <v-btn value="editor" title="Editor">
              <v-icon>mdi-pencil</v-icon>
            </v-btn>
            <v-btn value="split" title="Split">
              <v-icon>mdi-view-split-vertical</v-icon>
            </v-btn>
            <v-btn value="preview" title="Preview">
              <v-icon>mdi-eye-outline</v-icon>
            </v-btn>
          </v-btn-toggle>
        </div>

        <v-divider />

        <div class="content-body">
          <div v-if="isLoading('document')" class="document-loading-overlay">
            <v-skeleton-loader
              type="card"
              class="document-loading-skeleton"
              height="320"
            />
          </div>

          <div class="h-100">
            <v-alert
              v-if="!hasPermission('feature:markdown_collab:view')"
              type="warning"
              variant="tonal"
              class="ma-4"
            >
              Dir fehlt die Berechtigung <code>feature:markdown_collab:view</code>.
            </v-alert>

            <v-alert
              v-else-if="!selectedNode || selectedNode.type !== 'file'"
              type="info"
              variant="tonal"
              class="ma-4"
            >
              Wähle links eine Markdown-Datei aus, um sie zu bearbeiten.
            </v-alert>

            <template v-else>
              <div class="editor-stack">
                <div class="pane-grid" :class="`mode-${viewMode}`">
                  <div class="pane editor-pane">
                    <MarkdownEditorPane
                      ref="editorRef"
                      :key="selectedNode.id"
                      :document="selectedNode"
                      :readonly="!hasPermission('feature:markdown_collab:edit')"
                      @content-change="onEditorContentChange"
                      @git-summary="(s) => (gitSummary = s)"
                    />
                  </div>
                  <div class="pane preview-pane">
                    <MarkdownPreviewPane :markdown="currentText" />
                  </div>
                </div>

                <MarkdownGitPanel
                  v-if="selectedNode && selectedNode.type === 'file'"
                  :document-id="selectedNode.id"
                  :summary="gitSummary"
                  :can-commit="hasPermission('feature:markdown_collab:edit')"
                  :get-content="() => editorRef?.getCurrentContent?.()"
                  @committed="refreshCommits"
                />
              </div>
            </template>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- Share / Members Dialog -->
    <v-dialog v-model="shareDialog" max-width="640">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-account-multiple-plus</v-icon>
          Workspace teilen
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" @click="shareDialog = false" />
        </v-card-title>
        <v-divider />

        <v-card-text>
          <v-alert v-if="shareError" type="error" variant="tonal" class="mb-4">
            {{ shareError }}
          </v-alert>

          <div class="text-caption text-medium-emphasis mb-2">
            Owner: <strong>{{ workspace?.owner_username || '—' }}</strong>
          </div>

          <v-combobox
            v-model="inviteUsername"
            v-model:search="inviteSearch"
            :items="userSuggestions"
            :loading="userSearchLoading"
            label="Nutzer hinzufügen"
            variant="outlined"
            density="comfortable"
            clearable
            hide-details
          />

          <div class="d-flex justify-end mt-3">
            <v-btn
              color="primary"
              :loading="inviting"
              :disabled="!inviteUsername || inviting"
              @click="inviteMember"
            >
              Hinzufügen
            </v-btn>
          </div>

          <v-divider class="my-4" />

          <div class="text-subtitle-2 mb-2">Mitglieder</div>
          <v-skeleton-loader v-if="membersLoading" type="list-item@4" />
          <v-alert
            v-else-if="members.length === 0"
            type="info"
            variant="tonal"
          >
            Noch keine eingeladenen Mitglieder.
          </v-alert>
          <v-list v-else density="compact">
            <v-list-item v-for="m in members" :key="m.username">
              <v-list-item-title>{{ m.username }}</v-list-item-title>
              <v-list-item-subtitle v-if="m.added_at">
                hinzugefügt: {{ formatDate(m.added_at) }}
              </v-list-item-subtitle>
              <template #append>
                <v-btn
                  v-if="canShareWorkspace"
                  icon="mdi-delete"
                  variant="text"
                  color="error"
                  :loading="removingUsername === m.username"
                  @click="removeMember(m.username)"
                />
              </template>
            </v-list-item>
          </v-list>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { computed, onMounted, ref, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { usePermissions } from '@/composables/usePermissions'
import MarkdownTreePanel from '@/components/MarkdownCollab/MarkdownTreePanel.vue'
import MarkdownEditorPane from '@/components/MarkdownCollab/MarkdownEditorPane.vue'
import MarkdownPreviewPane from '@/components/MarkdownCollab/MarkdownPreviewPane.vue'
import MarkdownGitPanel from '@/components/MarkdownCollab/MarkdownGitPanel.vue'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

const route = useRoute()
const router = useRouter()

const { hasPermission, fetchPermissions, username: currentUsername, isAdmin } = usePermissions()
const { isLoading, withLoading, setLoading } = useSkeletonLoading(['tree', 'document'])

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080'
const VIEWMODE_KEY = 'markdown-collab-view-mode'

const workspace = ref(null)
const nodesFlat = ref([])

const currentText = ref('')
const gitSummary = ref({ users: [], totalChangedLines: 0 })
const editorRef = ref(null)
const pendingDocId = ref(null)

// Sharing / members
const shareDialog = ref(false)
const members = ref([])
const membersLoading = ref(false)
const shareError = ref('')
const inviting = ref(false)
const removingUsername = ref('')
const inviteUsername = ref('')
const inviteSearch = ref('')
const userSuggestions = ref([])
const userSearchLoading = ref(false)

const viewMode = ref(localStorage.getItem(VIEWMODE_KEY) || 'split')
watch(viewMode, (val) => localStorage.setItem(VIEWMODE_KEY, val))
watch(viewMode, async () => {
  await nextTick()
  editorRef.value?.refresh?.()
})

const workspaceId = computed(() => Number(route.params.workspaceId))
const routeDocId = computed(() => (route.params.documentId ? Number(route.params.documentId) : null))

const selectedNodeId = computed(() => routeDocId.value)
const selectedNode = computed(() => {
  if (!selectedNodeId.value) return null
  return nodesFlat.value.find(n => n.id === selectedNodeId.value) || null
})

const canShareWorkspace = computed(() => {
  if (!workspace.value) return false
  if (!hasPermission('feature:markdown_collab:share')) return false
  return isAdmin.value || (currentUsername.value && currentUsername.value === workspace.value.owner_username)
})

function onEditorContentChange(text) {
  currentText.value = text
  if (pendingDocId.value && pendingDocId.value === selectedNodeId.value) {
    setLoading('document', false)
    pendingDocId.value = null
  }
}

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

async function loadMembers() {
  if (!workspaceId.value) return
  membersLoading.value = true
  shareError.value = ''
  try {
    const res = await axios.get(`${API_BASE}/api/markdown-collab/workspaces/${workspaceId.value}/members`, {
      headers: authHeaders()
    })
    members.value = res.data.members || []
  } catch (e) {
    members.value = []
    shareError.value = e?.response?.data?.error || e?.message || 'Mitglieder konnten nicht geladen werden'
  } finally {
    membersLoading.value = false
  }
}

function openShareDialog() {
  shareDialog.value = true
  inviteUsername.value = ''
  inviteSearch.value = ''
  userSuggestions.value = []
  loadMembers()
}

async function inviteMember() {
  if (!inviteUsername.value) return
  inviting.value = true
  shareError.value = ''
  try {
    await axios.post(
      `${API_BASE}/api/markdown-collab/workspaces/${workspaceId.value}/members`,
      { username: String(inviteUsername.value).trim() },
      { headers: authHeaders() }
    )
    inviteUsername.value = ''
    inviteSearch.value = ''
    await loadMembers()
  } catch (e) {
    shareError.value = e?.response?.data?.error || e?.message || 'Einladung fehlgeschlagen'
  } finally {
    inviting.value = false
  }
}

async function removeMember(username) {
  if (!username) return
  removingUsername.value = username
  shareError.value = ''
  try {
    await axios.delete(`${API_BASE}/api/markdown-collab/workspaces/${workspaceId.value}/members/${encodeURIComponent(username)}`, {
      headers: authHeaders()
    })
    await loadMembers()
  } catch (e) {
    shareError.value = e?.response?.data?.error || e?.message || 'Entfernen fehlgeschlagen'
  } finally {
    removingUsername.value = ''
  }
}

let suggestionTimer = null
watch(inviteSearch, (q) => {
  if (suggestionTimer) clearTimeout(suggestionTimer)
  const query = String(q || '').trim()
  if (query.length < 2) {
    userSuggestions.value = []
    userSearchLoading.value = false
    return
  }
  suggestionTimer = setTimeout(async () => {
    userSearchLoading.value = true
    try {
      const res = await axios.get(`${API_BASE}/api/users/search`, {
        headers: authHeaders(),
        params: { q: query, limit: 10 }
      })
      const users = res.data.users || []
      userSuggestions.value = users.map(u => u.username).filter(Boolean)
    } catch (e) {
      userSuggestions.value = []
    } finally {
      userSearchLoading.value = false
    }
  }, 250)
})

function buildTree(flat) {
  const byId = new Map(flat.map(n => [n.id, { ...n, children: [] }]))
  const roots = []
  for (const node of byId.values()) {
    if (node.parent_id == null) {
      roots.push(node)
      continue
    }
    const parent = byId.get(node.parent_id)
    if (parent) parent.children.push(node)
    else roots.push(node)
  }
  const sortRec = (arr) => {
    arr.sort((a, b) => (a.order_index ?? 0) - (b.order_index ?? 0) || a.id - b.id)
    arr.forEach(n => sortRec(n.children))
  }
  sortRec(roots)
  return roots
}

const treeNodes = computed(() => buildTree(nodesFlat.value))

async function loadTree() {
  await withLoading('tree', async () => {
    const res = await axios.get(`${API_BASE}/api/markdown-collab/workspaces/${workspaceId.value}/tree`, {
      headers: authHeaders()
    })
    workspace.value = res.data.workspace
    nodesFlat.value = (res.data.nodes || []).map(n => ({ ...n, type: n.type }))
  })
}

function handleSelectNode(nodeId) {
  const node = nodesFlat.value.find(n => n.id === nodeId)
  if (!node) return

  if (node.type === 'file') {
    router.push(`/MarkdownCollab/workspace/${workspaceId.value}/document/${node.id}`)
    return
  }

  // Folder: keep workspace route, but don't force a document selection
  router.push(`/MarkdownCollab/workspace/${workspaceId.value}`)
}

async function handleCreateNode({ parentId, type, title }) {
  if (!hasPermission('feature:markdown_collab:edit')) return
  await axios.post(
    `${API_BASE}/api/markdown-collab/documents`,
    {
      workspace_id: workspaceId.value,
      parent_id: parentId ?? null,
      type,
      title
    },
    { headers: authHeaders() }
  )
  await loadTree()
}

async function handleRenameNode({ id, parentId, title }) {
  if (!hasPermission('feature:markdown_collab:edit')) return
  await axios.patch(
    `${API_BASE}/api/markdown-collab/documents/${id}`,
    { parent_id: parentId ?? null, title },
    { headers: authHeaders() }
  )
  await loadTree()
}

async function handleDeleteNode({ id }) {
  if (!hasPermission('feature:markdown_collab:edit')) return
  await axios.delete(`${API_BASE}/api/markdown-collab/documents/${id}`, {
    headers: authHeaders()
  })
  const onDocRoute = !!routeDocId.value && routeDocId.value === id
  if (onDocRoute) {
    router.push(`/MarkdownCollab/workspace/${workspaceId.value}`)
  }
  await loadTree()
}

async function handleMoveNode({ id, parentId, orderIndex }) {
  if (!hasPermission('feature:markdown_collab:edit')) return
  await axios.patch(
    `${API_BASE}/api/markdown-collab/documents/${id}`,
    { parent_id: parentId ?? null, order_index: orderIndex },
    { headers: authHeaders() }
  )
  await loadTree()
}

async function refreshCommits() {
  // Refresh the git baseline after commit to update diff decorations
  await editorRef.value?.refreshBaseline?.()
  editorRef.value?.clearHighlights?.()
}

watch(
  selectedNodeId,
  (docId) => {
    currentText.value = ''
    gitSummary.value = { users: [], totalChangedLines: 0, hasChanges: false, insertions: 0, deletions: 0 }
    if (docId) {
      pendingDocId.value = docId
      setLoading('document', true)
    } else {
      pendingDocId.value = null
      setLoading('document', false)
    }
  },
  { immediate: true }
)

onMounted(async () => {
  await fetchPermissions()
  await loadTree()

  // Auto-select first file if none selected
  if (!routeDocId.value) {
    const firstFile = nodesFlat.value.find(n => n.type === 'file')
    if (firstFile) router.replace(`/MarkdownCollab/workspace/${workspaceId.value}/document/${firstFile.id}`)
  }
})
</script>

<style scoped>
.workspace-root {
  height: calc(100vh - 94px);
  background-color: rgb(var(--v-theme-background));
}

.tree-col {
  height: 100%;
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgb(var(--v-theme-surface));
}

.content-col {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-background));
}

.content-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
}

.mode-toggle :deep(.v-btn) {
  min-width: 44px;
}

.content-body {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.document-loading-overlay {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  justify-content: center;
  padding: 16px;
  background: rgba(var(--v-theme-background), 0.55);
}

.document-loading-skeleton {
  width: 100%;
  max-width: 980px;
}

.pane-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 12px;
  overflow: hidden;
}

.editor-stack {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.pane {
  min-height: 0;
  overflow: hidden;
}

.mode-editor {
  grid-template-columns: 1fr;
}

.mode-editor .preview-pane {
  display: none;
}

.mode-preview {
  grid-template-columns: 1fr;
}

.mode-preview .editor-pane {
  display: none;
}
</style>
