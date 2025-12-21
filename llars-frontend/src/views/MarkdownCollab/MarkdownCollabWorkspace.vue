<template>
  <div class="workspace-root">
    <!-- Collapsible File Tree -->
    <div
      class="tree-panel"
      :class="{ collapsed: treeCollapsed }"
      :style="!treeCollapsed ? { width: treePanelWidth + 'px' } : {}"
    >
      <!-- Collapsed State -->
      <div v-if="treeCollapsed" class="tree-collapsed" @click="treeCollapsed = false">
        <div class="collapsed-bar">
          <div class="collapsed-icon-box">
            <v-icon size="18">mdi-file-tree</v-icon>
          </div>
          <span class="collapsed-label">Dateien</span>
          <v-spacer />
          <v-icon size="18" class="expand-icon">mdi-chevron-right</v-icon>
        </div>
      </div>

      <!-- Expanded State -->
      <div v-else class="tree-expanded">
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
        >
          <template #header-append>
            <v-btn
              icon
              variant="text"
              size="small"
              title="Einklappen"
              @click.stop="treeCollapsed = true"
            >
              <v-icon size="18">mdi-chevron-left</v-icon>
            </v-btn>
          </template>
        </MarkdownTreePanel>
      </div>
    </div>

    <!-- Resize Divider: Tree | Content -->
    <div
      v-if="!treeCollapsed"
      class="resize-divider vertical"
      :class="{ resizing: resizingTree }"
      @mousedown="startTreeResize"
    >
      <div class="resize-handle" />
    </div>

    <!-- Main Content Area -->
    <div class="content-area">
      <!-- Content Header -->
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

      <!-- Content Body -->
      <div class="content-body">
        <div v-if="isLoading('document')" class="document-loading-overlay">
          <v-skeleton-loader
            type="card"
            class="document-loading-skeleton"
            height="320"
          />
        </div>

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
          <div class="editor-layout">
            <!-- Editor/Preview Panes -->
            <div ref="panesContainerRef" class="panes-container" :class="`mode-${viewMode}`">
              <!-- Editor Pane -->
              <div
                class="pane editor-pane"
                :style="viewMode === 'split' ? { width: editorPaneWidth + 'px' } : {}"
              >
                <MarkdownEditorPane
                  ref="editorRef"
                  :key="selectedNode.id"
                  :document="selectedNode"
                  :readonly="!hasPermission('feature:markdown_collab:edit')"
                  @content-change="onEditorContentChange"
                  @git-summary="(s) => (gitSummary = s)"
                />
              </div>

              <!-- Resize Divider: Editor | Preview -->
              <div
                v-if="viewMode === 'split'"
                class="resize-divider vertical"
                :class="{ resizing: resizingPanes }"
                @mousedown="startPanesResize"
              >
                <div class="resize-handle" />
              </div>

              <!-- Preview Pane -->
              <div class="pane preview-pane">
                <MarkdownPreviewPane :markdown="currentText" />
              </div>
            </div>

            <!-- Git Panel -->
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
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch, nextTick } from 'vue'
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
const TREE_COLLAPSED_KEY = 'markdown-collab-tree-collapsed'
const TREE_WIDTH_KEY = 'markdown-collab-tree-width'
const PANES_WIDTH_KEY = 'markdown-collab-panes-width'

const workspace = ref(null)
const nodesFlat = ref([])

const currentText = ref('')
const gitSummary = ref({ users: [], totalChangedLines: 0 })
const editorRef = ref(null)
const pendingDocId = ref(null)

// Panel states
const treeCollapsed = ref(localStorage.getItem(TREE_COLLAPSED_KEY) === 'true')
const treePanelWidth = ref(parseInt(localStorage.getItem(TREE_WIDTH_KEY)) || 280)
const editorPaneWidth = ref(parseInt(localStorage.getItem(PANES_WIDTH_KEY)) || 0)
const panesContainerRef = ref(null)

// Resize states
const resizingTree = ref(false)
const resizingPanes = ref(false)

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

watch(viewMode, (val) => {
  localStorage.setItem(VIEWMODE_KEY, val)
  // Reset pane width when switching modes
  if (val === 'split' && panesContainerRef.value) {
    editorPaneWidth.value = panesContainerRef.value.offsetWidth / 2
  }
})

watch(viewMode, async () => {
  await nextTick()
  editorRef.value?.refresh?.()
})

watch(treeCollapsed, (val) => {
  localStorage.setItem(TREE_COLLAPSED_KEY, val.toString())
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

// Tree panel resize
function startTreeResize(event) {
  event.preventDefault()
  resizingTree.value = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  document.addEventListener('mousemove', onTreeMouseMove)
  document.addEventListener('mouseup', stopTreeResize)
}

function onTreeMouseMove(event) {
  if (!resizingTree.value) return
  // Allow very small widths (min 48px for icon-only mode), max 600px
  const newWidth = Math.max(48, Math.min(600, event.clientX))
  treePanelWidth.value = newWidth
}

function stopTreeResize() {
  resizingTree.value = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  document.removeEventListener('mousemove', onTreeMouseMove)
  document.removeEventListener('mouseup', stopTreeResize)
  localStorage.setItem(TREE_WIDTH_KEY, treePanelWidth.value.toString())
}

// Panes resize (Editor | Preview)
function startPanesResize(event) {
  event.preventDefault()
  resizingPanes.value = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  document.addEventListener('mousemove', onPanesMouseMove)
  document.addEventListener('mouseup', stopPanesResize)
}

function onPanesMouseMove(event) {
  if (!resizingPanes.value || !panesContainerRef.value) return
  const containerRect = panesContainerRef.value.getBoundingClientRect()
  const mouseX = event.clientX - containerRect.left
  const containerWidth = containerRect.width
  // Clamp between 25% and 75%
  const minWidth = containerWidth * 0.25
  const maxWidth = containerWidth * 0.75
  editorPaneWidth.value = Math.max(minWidth, Math.min(maxWidth, mouseX))
}

function stopPanesResize() {
  resizingPanes.value = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  document.removeEventListener('mousemove', onPanesMouseMove)
  document.removeEventListener('mouseup', stopPanesResize)
  localStorage.setItem(PANES_WIDTH_KEY, editorPaneWidth.value.toString())
}

// Initialize pane width on mount
onMounted(async () => {
  await fetchPermissions()
  await loadTree()

  // Auto-select first file if none selected
  if (!routeDocId.value) {
    const firstFile = nodesFlat.value.find(n => n.type === 'file')
    if (firstFile) router.replace(`/MarkdownCollab/workspace/${workspaceId.value}/document/${firstFile.id}`)
  }

  // Initialize editor pane width
  await nextTick()
  if (panesContainerRef.value && editorPaneWidth.value === 0) {
    editorPaneWidth.value = panesContainerRef.value.offsetWidth / 2
  }
})

onUnmounted(() => {
  document.removeEventListener('mousemove', onTreeMouseMove)
  document.removeEventListener('mouseup', stopTreeResize)
  document.removeEventListener('mousemove', onPanesMouseMove)
  document.removeEventListener('mouseup', stopPanesResize)
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
</script>

<style scoped>
/* LLARS Design Variables */
.workspace-root {
  --llars-primary: #b0ca97;
  --llars-accent: #88c4c8;
  --llars-radius: 16px 4px 16px 4px;
  --llars-radius-sm: 8px 2px 8px 2px;

  height: calc(100vh - 94px);
  display: flex;
  background-color: rgb(var(--v-theme-background));
  overflow: hidden;
}

/* ============================================
   TREE PANEL
   ============================================ */
.tree-panel {
  flex-shrink: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  transition: width 0.2s ease;
  min-width: 0;
  overflow: hidden;
}

.tree-panel.collapsed {
  width: 48px !important;
}

.tree-expanded {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

/* Collapsed Tree */
.tree-collapsed {
  height: 100%;
  cursor: pointer;
}

.collapsed-bar {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  gap: 12px;
  background: linear-gradient(180deg, var(--llars-primary) 0%, var(--llars-accent) 100%);
}

.collapsed-icon-box {
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 6px 2px 6px 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.collapsed-label {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  font-weight: 600;
  font-size: 13px;
  color: white;
  letter-spacing: 1px;
}

.expand-icon {
  color: white;
  opacity: 0.8;
  margin-top: auto;
}

/* ============================================
   RESIZE DIVIDER
   ============================================ */
.resize-divider {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}

.resize-divider.vertical {
  width: 6px;
  cursor: col-resize;
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.resize-divider.vertical:hover,
.resize-divider.vertical.resizing {
  background: rgba(var(--v-theme-primary), 0.15);
}

.resize-handle {
  width: 3px;
  height: 40px;
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 2px;
  transition: background 0.15s, height 0.15s;
}

.resize-divider:hover .resize-handle,
.resize-divider.resizing .resize-handle {
  background: rgb(var(--v-theme-primary));
  height: 60px;
}

/* ============================================
   CONTENT AREA
   ============================================ */
.content-area {
  flex: 1;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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
  display: flex;
  flex-direction: column;
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

/* ============================================
   EDITOR LAYOUT
   ============================================ */
.editor-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 8px;
  gap: 8px;
  overflow: hidden;
}

.panes-container {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0;
}

.pane {
  min-height: 0;
  overflow: hidden;
}

/* Split mode */
.panes-container.mode-split .editor-pane {
  flex-shrink: 0;
}

.panes-container.mode-split .preview-pane {
  flex: 1;
  min-width: 0;
}

/* Editor only mode */
.panes-container.mode-editor {
  flex-direction: column;
}

.panes-container.mode-editor .editor-pane {
  flex: 1;
  width: 100% !important;
}

.panes-container.mode-editor .preview-pane {
  display: none;
}

/* Preview only mode */
.panes-container.mode-preview {
  flex-direction: column;
}

.panes-container.mode-preview .editor-pane {
  display: none;
}

.panes-container.mode-preview .preview-pane {
  flex: 1;
}
</style>
