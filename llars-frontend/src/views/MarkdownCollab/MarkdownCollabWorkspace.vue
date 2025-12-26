<template>
  <div class="workspace-root" :class="{ 'is-mobile': isMobile, 'is-tablet': isTablet }">
    <!-- Mobile Navigation Drawer -->
    <v-navigation-drawer
      v-if="isMobile"
      v-model="mobileSidebarOpen"
      temporary
      width="300"
      class="mobile-tree-drawer"
    >
      <MarkdownTreePanel
        :workspace-id="workspaceId"
        :nodes="treeNodes"
        :selected-id="selectedNodeId"
        :loading="isLoading('tree')"
        :can-edit="hasPermission('feature:markdown_collab:edit')"
        :recently-added-ids="recentlyAddedNodeIds"
        @select="(id) => { handleSelectNode(id); mobileSidebarOpen = false; }"
        @create="handleCreateNode"
        @rename="handleRenameNode"
        @remove="handleDeleteNode"
        @move="handleMoveNode"
      />
      <template #append>
        <v-divider />
        <v-list density="compact" class="pa-2">
          <v-list-item
            prepend-icon="mdi-home"
            title="Startseite"
            @click="router.push('/Home')"
          />
          <v-list-item
            prepend-icon="mdi-folder-multiple"
            title="Alle Workspaces"
            @click="router.push('/MarkdownCollab')"
          />
        </v-list>
      </template>
    </v-navigation-drawer>

    <!-- Desktop: Collapsible File Tree -->
    <div
      v-if="!isMobile"
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
          :recently-added-ids="recentlyAddedNodeIds"
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

    <!-- Resize Divider: Tree | Content (Desktop only) -->
    <div
      v-if="!isMobile && !treeCollapsed"
      class="resize-divider vertical"
      :class="{ resizing: resizingTree }"
      @mousedown="startTreeResize"
    >
      <div class="resize-handle" />
    </div>

    <!-- Main Content Area -->
    <div class="content-area">
      <!-- Content Header - Subtle LLARS Design -->
      <div class="content-header">
        <div class="header-left">
          <!-- Mobile menu button -->
          <v-btn
            v-if="isMobile"
            icon
            variant="text"
            size="small"
            class="mr-2"
            @click="mobileSidebarOpen = true"
          >
            <v-icon>mdi-menu</v-icon>
          </v-btn>
          <v-btn
            variant="text"
            size="small"
            class="header-back-btn"
            title="Zurück zu den Workspaces"
            @click="router.push('/MarkdownCollab')"
          >
            <v-icon size="18">mdi-arrow-left</v-icon>
            <span v-if="!isMobile" class="header-back-label">Workspaces</span>
          </v-btn>
          <v-icon v-if="!isMobile" size="20" color="primary" class="mr-2">mdi-language-markdown</v-icon>
          <div class="header-info">
            <div class="header-title">{{ selectedNode?.title || 'Kein Dokument' }}</div>
            <div class="header-subtitle">{{ workspace?.name || `Workspace #${workspaceId}` }}</div>
          </div>
        </div>

        <div class="header-actions">
          <v-btn
            v-if="canShareWorkspace"
            icon
            variant="text"
            size="small"
            title="Workspace teilen"
            @click="openShareDialog"
          >
            <v-icon size="20">mdi-account-multiple-plus</v-icon>
          </v-btn>

          <div class="mode-toggle-group">
            <button
              class="mode-btn"
              :class="{ active: viewMode === 'editor' }"
              title="Editor"
              @click="viewMode = 'editor'"
            >
              <v-icon size="18">mdi-pencil</v-icon>
            </button>
            <button
              class="mode-btn"
              :class="{ active: viewMode === 'split' }"
              title="Split"
              @click="viewMode = 'split'"
            >
              <v-icon size="18">mdi-view-split-vertical</v-icon>
            </button>
            <button
              class="mode-btn"
              :class="{ active: viewMode === 'preview' }"
              title="Preview"
              @click="viewMode = 'preview'"
            >
              <v-icon size="18">mdi-eye-outline</v-icon>
            </button>
          </div>
        </div>
      </div>

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
                :style="editorPaneStyle"
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
              <div class="pane preview-pane" :style="previewPaneStyle">
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

    <!-- Share / Members Dialog - Subtle Design -->
    <v-dialog v-model="shareDialog" max-width="480">
      <v-card class="share-dialog">
        <v-card-title class="share-header">
          <v-icon class="mr-2" color="primary">mdi-account-multiple-plus</v-icon>
          <div>
            <div>Workspace teilen</div>
            <div class="text-caption text-medium-emphasis">{{ workspace?.name }}</div>
          </div>
          <v-spacer />
          <LIconBtn icon="mdi-close" tooltip="Schließen" size="small" @click="shareDialog = false" />
        </v-card-title>

        <v-divider />

        <v-card-text class="share-body">
          <v-alert v-if="shareError" type="error" variant="tonal" class="mb-4" density="compact">
            {{ shareError }}
          </v-alert>

          <!-- Owner Section -->
          <div class="section-label">Owner</div>
          <div class="user-card owner-card">
            <img class="user-avatar" :src="getAvatarUrl(ownerInfo)" alt="" />
            <div class="user-info">
              <div class="user-name">{{ formatDisplayName(ownerInfo.username) }}</div>
              <div class="user-meta">@{{ ownerInfo.username }}</div>
            </div>
            <LTag variant="primary" size="small">Owner</LTag>
          </div>

          <!-- Search Section -->
          <div class="section-label mt-4">Nutzer einladen</div>
          <LUserSearch
            ref="userSearchRef"
            v-model="selectedUser"
            :exclude-usernames="excludedUsernames"
            :show-add-button="true"
            add-button-text="Hinzufügen"
            @add="inviteMember"
          />

          <!-- Members Section -->
          <div class="section-label mt-4">
            Mitglieder
            <span v-if="members.length" class="member-count">{{ members.length }}</span>
          </div>

          <v-skeleton-loader v-if="membersLoading" type="list-item-avatar@3" />

          <div v-else-if="members.length === 0" class="empty-members">
            <v-icon size="28" color="grey-lighten-1">mdi-account-group-outline</v-icon>
            <span>Noch keine Mitglieder</span>
          </div>

          <div v-else class="members-list">
            <div v-for="m in members" :key="m.username" class="user-card">
              <img class="user-avatar" :src="getAvatarUrl(m)" alt="" />
              <div class="user-info">
                <div class="user-name">{{ formatDisplayName(m.username) }}</div>
                <div class="user-meta">{{ formatRelativeDate(m.added_at) }}</div>
              </div>
              <v-btn
                v-if="canShareWorkspace"
                icon
                variant="text"
                size="x-small"
                color="error"
                :loading="removingUsername === m.username"
                @click="removeMember(m.username)"
              >
                <v-icon size="18">mdi-close</v-icon>
              </v-btn>
            </div>
          </div>
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
import { useMobile } from '@/composables/useMobile'
import { useSplitPaneResize } from '@/composables/useSplitPaneResize'
import { useWorkspaceSocket } from '@/components/MarkdownCollab/composables/useWorkspaceSocket'
import { useActiveDuration, useVisibilityTracker, useScrollDepth } from '@/composables/useAnalyticsMetrics'
import MarkdownTreePanel from '@/components/MarkdownCollab/MarkdownTreePanel.vue'
import MarkdownEditorPane from '@/components/MarkdownCollab/MarkdownEditorPane.vue'
import MarkdownPreviewPane from '@/components/MarkdownCollab/MarkdownPreviewPane.vue'
import MarkdownGitPanel from '@/components/MarkdownCollab/MarkdownGitPanel.vue'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'
import { getAvatarUrl, formatDisplayName, formatRelativeDate } from '@/utils/userUtils'

const route = useRoute()
const router = useRouter()

const { hasPermission, fetchPermissions, username: currentUsername, isAdmin } = usePermissions()
const { isLoading, withLoading, setLoading } = useSkeletonLoading(['tree', 'document'])
const { isMobile, isTablet } = useMobile()

// Mobile sidebar state
const mobileSidebarOpen = ref(false)

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
const viewMode = ref(localStorage.getItem(VIEWMODE_KEY) || 'split')
const resizingTree = ref(false)
const {
  panesContainerRef,
  editorPaneStyle,
  previewPaneStyle,
  resizingPanes,
  startResize: startPanesResize
} = useSplitPaneResize({
  storageKey: PANES_WIDTH_KEY,
  viewMode
})

// Sharing / members
const shareDialog = ref(false)
const members = ref([])
const membersLoading = ref(false)
const shareError = ref('')
const removingUsername = ref('')
const selectedUser = ref(null)
const userSearchRef = ref(null)
const ownerInfo = ref({ username: '', avatar_url: null, avatar_seed: null, collab_color: null })

// Analytics: entity dimension for this workspace/document
const workspaceEntity = computed(() => `ws:${workspaceId.value}`)
const documentEntity = computed(() => selectedNodeId.value ? `doc:${selectedNodeId.value}` : '')

// Session active time tracking
useActiveDuration({
  category: 'markdown',
  action: 'session_active_ms',
  name: () => workspaceEntity.value,
  dimensions: () => ({ entity: workspaceEntity.value, view: viewMode.value })
})

// Pane visibility tracking (editor, preview)
const paneVisibility = useVisibilityTracker({
  category: 'markdown',
  action: 'pane_visible_ms',
  nameBuilder: (id) => `pane:${id}`,
  dimensions: () => ({ entity: documentEntity.value })
})

// Scroll depth for panes container
useScrollDepth(panesContainerRef, {
  category: 'markdown',
  action: 'scroll_depth',
  name: () => `${documentEntity.value}|${viewMode.value}`,
  dimensions: () => ({ entity: documentEntity.value, view: viewMode.value })
})

// Register panes for visibility tracking
watch(panesContainerRef, (el) => {
  if (el) {
    paneVisibility.register('panes', el, { view: viewMode.value })
  }
})

watch(viewMode, (val) => {
  localStorage.setItem(VIEWMODE_KEY, val)
  // Pane width is handled by CSS (flex: 1 1 50%) by default
  // or by saved localStorage value when user has manually resized
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

// Workspace socket for real-time tree updates
const {
  isConnected: wsConnected,
  recentlyAddedNodeIds,
  connect: wsConnect,
  emitNodeCreated,
  emitNodeRenamed,
  emitNodeDeleted,
  emitNodeMoved
} = useWorkspaceSocket(workspaceId, {
  onNodeCreated: (data) => {
    // Add the new node to the tree
    const newNode = { ...data.node, type: data.node.type }
    nodesFlat.value = [...nodesFlat.value, newNode]
  },
  onNodeRenamed: (data) => {
    // Update the node title in the tree
    const node = nodesFlat.value.find(n => n.id === data.nodeId)
    if (node) {
      node.title = data.newTitle
      nodesFlat.value = [...nodesFlat.value]
    }
  },
  onNodeDeleted: (data) => {
    // Remove the node from the tree (and children recursively)
    const removeRecursive = (nodeId) => {
      const children = nodesFlat.value.filter(n => n.parent_id === nodeId)
      children.forEach(c => removeRecursive(c.id))
      nodesFlat.value = nodesFlat.value.filter(n => n.id !== nodeId)
    }
    removeRecursive(data.nodeId)

    // If we're viewing the deleted document, navigate away
    if (routeDocId.value === data.nodeId) {
      router.push(`/MarkdownCollab/workspace/${workspaceId.value}`)
    }
  },
  onNodeMoved: (data) => {
    // Update node position in tree
    const node = nodesFlat.value.find(n => n.id === data.nodeId)
    if (node) {
      node.parent_id = data.newParentId
      node.order_index = data.newOrderIndex
      nodesFlat.value = [...nodesFlat.value]
    }
  }
})

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

// Usernames to exclude from search (owner + existing members)
const excludedUsernames = computed(() => {
  const excluded = []
  if (workspace.value?.owner_username) excluded.push(workspace.value.owner_username)
  members.value.forEach(m => excluded.push(m.username))
  return excluded
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

// Initialize pane width on mount
onMounted(async () => {
  await fetchPermissions()
  await loadTree()

  // Connect to workspace socket for real-time tree updates
  wsConnect()

  // Auto-select first file if none selected
  if (!routeDocId.value) {
    const firstFile = nodesFlat.value.find(n => n.type === 'file')
    if (firstFile) router.replace(`/MarkdownCollab/workspace/${workspaceId.value}/document/${firstFile.id}`)
  }

  // Editor pane width is now handled by CSS (flex: 1 1 50%) by default
  // Only apply saved width from localStorage when user has manually resized
})

onUnmounted(() => {
  document.removeEventListener('mousemove', onTreeMouseMove)
  document.removeEventListener('mouseup', stopTreeResize)
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
    // Store owner info
    ownerInfo.value = {
      username: res.data.owner_username || '',
      avatar_url: res.data.owner_avatar_url || null,
      avatar_seed: res.data.owner_avatar_seed || null,
      collab_color: res.data.owner_collab_color || null
    }
  } catch (e) {
    members.value = []
    shareError.value = e?.response?.data?.error || e?.message || 'Mitglieder konnten nicht geladen werden'
  } finally {
    membersLoading.value = false
  }
}

// Helper functions for user display imported from @/utils/userUtils

function openShareDialog() {
  shareDialog.value = true
  selectedUser.value = null
  loadMembers()
}

async function inviteMember(user) {
  const username = user?.username || selectedUser.value?.username
  if (!username) return
  shareError.value = ''
  try {
    await axios.post(
      `${API_BASE}/api/markdown-collab/workspaces/${workspaceId.value}/members`,
      { username: username.trim() },
      { headers: authHeaders() }
    )
    selectedUser.value = null
    userSearchRef.value?.reset?.()
    await loadMembers()
  } catch (e) {
    shareError.value = e?.response?.data?.error || e?.message || 'Einladung fehlgeschlagen'
    userSearchRef.value?.setAdding?.(false)
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
  try {
    const res = await axios.post(
      `${API_BASE}/api/markdown-collab/documents`,
      {
        workspace_id: workspaceId.value,
        parent_id: parentId ?? null,
        type,
        title
      },
      { headers: authHeaders() }
    )

    // Add node to local tree immediately
    const newNode = res.data.node
    if (newNode) {
      nodesFlat.value = [...nodesFlat.value, { ...newNode, type: newNode.type }]
      // Broadcast to other users
      emitNodeCreated(newNode)
    }
  } catch (e) {
    console.error('Failed to create node:', e)
    await loadTree() // Fallback: reload tree
  }
}

async function handleRenameNode({ id, parentId, title }) {
  if (!hasPermission('feature:markdown_collab:edit')) return
  try {
    await axios.patch(
      `${API_BASE}/api/markdown-collab/documents/${id}`,
      { parent_id: parentId ?? null, title },
      { headers: authHeaders() }
    )

    // Update local tree immediately
    const node = nodesFlat.value.find(n => n.id === id)
    if (node) {
      node.title = title
      nodesFlat.value = [...nodesFlat.value]
      // Broadcast to other users
      emitNodeRenamed(id, title)
    }
  } catch (e) {
    console.error('Failed to rename node:', e)
    await loadTree() // Fallback: reload tree
  }
}

async function handleDeleteNode({ id }) {
  if (!hasPermission('feature:markdown_collab:edit')) return
  try {
    await axios.delete(`${API_BASE}/api/markdown-collab/documents/${id}`, {
      headers: authHeaders()
    })

    // Remove from local tree immediately (including children)
    const removeRecursive = (nodeId) => {
      const children = nodesFlat.value.filter(n => n.parent_id === nodeId)
      children.forEach(c => removeRecursive(c.id))
      nodesFlat.value = nodesFlat.value.filter(n => n.id !== nodeId)
    }
    removeRecursive(id)

    // Broadcast to other users
    emitNodeDeleted(id)

    // Navigate away if viewing deleted document
    if (routeDocId.value === id) {
      router.push(`/MarkdownCollab/workspace/${workspaceId.value}`)
    }
  } catch (e) {
    console.error('Failed to delete node:', e)
    await loadTree() // Fallback: reload tree
  }
}

async function handleMoveNode({ id, parentId, orderIndex }) {
  if (!hasPermission('feature:markdown_collab:edit')) return
  try {
    await axios.patch(
      `${API_BASE}/api/markdown-collab/documents/${id}`,
      { parent_id: parentId ?? null, order_index: orderIndex },
      { headers: authHeaders() }
    )

    // Update local tree immediately
    const node = nodesFlat.value.find(n => n.id === id)
    if (node) {
      node.parent_id = parentId ?? null
      node.order_index = orderIndex
      nodesFlat.value = [...nodesFlat.value]
      // Broadcast to other users
      emitNodeMoved(id, parentId ?? null, orderIndex)
    }
  } catch (e) {
    console.error('Failed to move node:', e)
    await loadTree() // Fallback: reload tree
  }
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

/* ============================================
   CONTENT HEADER - Subtle Design
   ============================================ */
.content-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  min-width: 0;
  flex: 1;
}

.header-info {
  min-width: 0;
  flex: 1;
}

.header-back-btn {
  margin-right: 6px;
}

.header-back-label {
  margin-left: 4px;
  font-size: 12px;
  text-transform: none;
}

.header-title {
  font-weight: 500;
  font-size: 14px;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: rgb(var(--v-theme-on-surface));
}

.header-subtitle {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.mode-toggle-group {
  display: flex;
  background: rgba(var(--v-theme-on-surface), 0.05);
  border-radius: 6px;
  padding: 2px;
}

.mode-btn {
  width: 30px;
  height: 30px;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(var(--v-theme-on-surface), 0.5);
  transition: all 0.15s ease;
}

.mode-btn:hover {
  color: rgba(var(--v-theme-on-surface), 0.8);
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.mode-btn.active {
  background: var(--llars-primary);
  color: white;
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

/* ============================================
   SHARE DIALOG - Subtle Design
   ============================================ */
.share-dialog {
  border-radius: 12px !important;
}

.share-header {
  display: flex;
  align-items: center;
}

.share-body {
  max-height: 50vh;
  overflow-y: auto;
}

.section-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.member-count {
  background: rgba(var(--v-theme-on-surface), 0.1);
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 8px;
  font-weight: 500;
}

/* User Avatar */
.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  flex-shrink: 0;
  object-fit: cover;
}

.user-avatar.small {
  width: 28px;
  height: 28px;
  border-radius: 6px;
}

.user-avatar.x-small {
  width: 22px;
  height: 22px;
  border-radius: 5px;
}

/* User Card */
.user-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.user-card.owner-card {
  background: rgba(var(--v-theme-primary), 0.04);
  border-color: rgba(var(--v-theme-primary), 0.12);
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 500;
  font-size: 13px;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.2;
}

.user-meta {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Members Section */
.empty-members {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 20px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 12px;
}

.members-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* ============================================
   MOBILE RESPONSIVE STYLES
   ============================================ */
.workspace-root.is-mobile {
  /* 64px AppBar + 24px Footer = 88px */
  height: calc(100vh - 88px);
  height: calc(100dvh - 88px);
  overflow: hidden;
  max-width: 100vw;
}

.mobile-tree-drawer {
  background-color: rgb(var(--v-theme-surface)) !important;
}

.mobile-tree-drawer :deep(.markdown-tree-panel) {
  height: 100%;
}

/* Mobile content area takes full width */
.workspace-root.is-mobile .content-area {
  width: 100%;
}

/* Mobile header adjustments */
.workspace-root.is-mobile .content-header {
  padding: 6px 8px;
}

.workspace-root.is-mobile .header-title {
  font-size: 13px;
}

.workspace-root.is-mobile .header-subtitle {
  font-size: 10px;
}

.workspace-root.is-mobile .mode-toggle-group {
  padding: 1px;
}

.workspace-root.is-mobile .mode-btn {
  width: 28px;
  height: 28px;
}

/* Mobile editor layout */
.workspace-root.is-mobile .editor-layout {
  padding: 4px;
  gap: 4px;
}

/* Mobile: On split mode, stack vertically instead of horizontal */
.workspace-root.is-mobile .panes-container.mode-split {
  flex-direction: column;
}

.workspace-root.is-mobile .panes-container.mode-split .editor-pane {
  width: 100% !important;
  flex: 1;
}

.workspace-root.is-mobile .panes-container.mode-split .preview-pane {
  flex: 1;
}

.workspace-root.is-mobile .panes-container.mode-split .resize-divider {
  display: none;
}

/* Hide Git panel on mobile in compact mode */
.workspace-root.is-mobile .git-panel {
  max-height: 120px;
}

/* Tablet adjustments */
.workspace-root.is-tablet .tree-panel {
  max-width: 240px;
}

/* Default 50/50 split - ensure panes container uses flexbox properly */
.panes-container.mode-split .editor-pane,
.panes-container.mode-split .preview-pane {
  flex: 1 1 50%;
  min-width: 0;
}
</style>
