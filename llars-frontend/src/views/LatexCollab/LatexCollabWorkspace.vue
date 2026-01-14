<template>
  <div class="workspace-root" :class="{ 'is-mobile': isMobile, 'is-tablet': isTablet }">
    <input
      ref="assetInputRef"
      type="file"
      class="asset-input"
      multiple
      @change="handleAssetFiles"
    />
    <!-- Tree Panel (Mobile Drawer + Desktop Sidebar) -->
    <LatexTreePanel
      :is-mobile="isMobile"
      v-model:mobile-open="mobileSidebarOpen"
      v-model:tree-collapsed="treeCollapsed"
      v-model:files-collapsed="filesCollapsed"
      v-model:git-collapsed="gitCollapsed"
      v-model:outline-collapsed="outlineCollapsed"
      :workspace-id="workspaceId"
      :nodes="treeNodes"
      :selected-id="selectedNodeId"
      :loading="isLoading('tree')"
      :can-edit="hasPermission('feature:latex_collab:edit')"
      :can-commit="hasPermission('feature:latex_collab:edit')"
      :recently-added-ids="recentlyAddedNodeIds"
      :tree-panel-width="treePanelWidth"
      :resizing-tree="resizingTree"
      :outline-flat-items="outlineFlatItems"
      :outline-empty-label="outlineEmptyLabel"
      :is-outline-item-collapsed="isOutlineItemCollapsed"
      @select="handleSelectNode"
      @create="handleCreateNode"
      @rename="handleRenameNode"
      @remove="handleDeleteNode"
      @move="handleMoveNode"
      @open-asset-picker="openAssetPicker"
      @start-tree-resize="startTreeResize"
      @navigate-home="router.push('/Home')"
      @navigate-workspaces="router.push(routeBase)"
      @toggle-outline-item="toggleOutlineItem"
      @jump-to-outline-item="jumpToOutlineItem"
      @open-git-detail="gitDetailDialog = true"
      @committed="refreshCommits"
    />

    <!-- Main Content Area -->
    <div class="content-area">
      <!-- Content Header -->
      <LatexContentHeader
        :is-mobile="isMobile"
        :document-title="selectedNode?.title || $t('latexCollab.workspace.empty.noDocument')"
        :workspace-name="workspace?.name || $t('latexCollab.workspace.fallbackName', { id: workspaceId })"
        :can-share="canShareWorkspace"
        :can-set-main="canSetMainDocument"
        :is-main-document="selectedNode?.id === workspace?.main_document_id"
        :review-mode="reviewMode"
        :show-connection-status="selectedNode?.type === 'file' && !selectedNode?.asset_id"
        :is-connected="editorRef?.isConnected"
        :ai-enabled="props.aiEnabled"
        :ghost-text-enabled="props.ghostTextEnabled"
        :active-users="editorRef?.activeUsers || []"
        v-model:view-mode="viewMode"
        @open-mobile-menu="mobileSidebarOpen = true"
        @navigate-back="router.push(routeBase)"
        @open-share="openShareDialog"
        @open-zotero="zoteroDialog = true"
        @set-main-document="setMainDocument"
        @toggle-review-mode="reviewMode = !reviewMode"
        @toggle-ghost-text="editorRef?.toggleGhostText?.()"
      />

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
          v-if="!hasPermission('feature:latex_collab:view')"
          type="warning"
        variant="tonal"
        class="ma-4"
      >
        <i18n-t keypath="latexCollab.permissions.missing" tag="span">
          <template #permission>
            <code>feature:latex_collab:view</code>
          </template>
        </i18n-t>
      </v-alert>

        <v-alert
          v-else-if="selectedNode && selectedNode.asset_id"
          type="info"
        variant="tonal"
        class="ma-4"
      >
        {{ $t('latexCollab.workspace.assetWarning') }}
      </v-alert>

        <v-alert
          v-else-if="!selectedNode || selectedNode.type !== 'file'"
          type="info"
        variant="tonal"
        class="ma-4"
      >
        {{ $t('latexCollab.workspace.empty.selectFile') }}
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
                <!-- Zotero read-only notice -->
                <v-alert
                  v-if="selectedNode?.is_zotero_managed"
                  type="info"
                  variant="tonal"
                  density="compact"
                  class="zotero-readonly-notice"
                >
                  <template #prepend>
                  <LIcon color="teal">mdi-bookshelf</LIcon>
                </template>
                <span class="text-body-2">
                  <i18n-t keypath="latexCollab.workspace.zoteroReadonly" tag="span">
                    <template #brand>
                      <strong>Zotero</strong>
                    </template>
                  </i18n-t>
                </span>
                </v-alert>
                <LatexEditorPane
                  ref="editorRef"
                  :document="selectedNode"
                  :readonly="editorReadonly"
                  :comments="comments"
                  :active-comment-id="activeCommentId"
                  :ai-enabled="props.aiEnabled"
                  :ghost-text-enabled="props.ghostTextEnabled"
                  :ghost-text-delay="props.ghostTextDelay"
                  @content-change="onEditorContentChange"
                  @git-summary="(s) => (gitSummary = s)"
                  @sync-request="handleEditorSyncRequest"
                  @ai-command="(cmd) => emit('ai-command', cmd)"
                  @ai-action="(e) => emit('ai-action', e)"
                  @request-completion="(req) => emit('request-completion', req)"
                  @update:ghost-text-enabled="(val) => emit('update:ghostTextEnabled', val)"
                  @document-saved="handleDocumentSaved"
                  @document-updated="handleDocumentUpdated"
                  @diff-calculated="handleDiffCalculated"
                  @request-comment="(range) => openCommentDialog(range)"
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
                <div class="preview-toolbar">
                  <div class="compile-actions">
                    <LBtn
                      variant="primary"
                      size="small"
                      :loading="isCompiling"
                      :disabled="!canCompile"
                      prepend-icon="mdi-rocket-launch-outline"
                      :title="$t('latexCollab.compile.actions.compile')"
                      @click="triggerCompile"
                    >
                      {{ $t('latexCollab.compile.actions.compile') }}
                    </LBtn>
                    <v-select
                      v-model="compileCommitId"
                      :items="compileCommitOptions"
                      :label="$t('latexCollab.compile.versionLabel')"
                      density="compact"
                      variant="outlined"
                      hide-details
                      class="compile-select"
                    />
                  </div>
                  <div class="compile-status">
                    <v-chip size="x-small" variant="tonal" :color="compileStatusColor">
                      {{ compileStatusLabel }}
                    </v-chip>
                    <v-btn
                      icon
                      variant="text"
                      size="x-small"
                      :title="$t('latexCollab.compile.actions.showLogs')"
                      @click="compileLogDialog = true"
                    >
                      <LIcon size="16">mdi-text-box-outline</LIcon>
                    </v-btn>
                    <v-menu>
                      <template #activator="{ props: menuProps }">
                        <v-btn icon variant="text" size="x-small" v-bind="menuProps" :title="$t('latexCollab.compile.auto.title')">
                          <LIcon size="16">mdi-tune-variant</LIcon>
                        </v-btn>
                      </template>
                      <v-card class="compile-settings">
                        <v-card-title class="text-subtitle-2">{{ $t('latexCollab.compile.auto.title') }}</v-card-title>
                        <v-card-text>
                      <v-switch
                        v-model="autoCompileEnabled"
                        :label="$t('latexCollab.compile.auto.enable')"
                        density="compact"
                        hide-details
                      />
                      <v-text-field
                        v-model.number="autoCompileDelay"
                        :label="$t('latexCollab.compile.auto.delayLabel')"
                        type="number"
                        min="500"
                        step="250"
                        variant="outlined"
                        density="compact"
                        hide-details
                      />
                      <v-switch
                        v-model="syncEnabled"
                        :label="$t('latexCollab.compile.auto.syncLabel')"
                        density="compact"
                        hide-details
                        :disabled="!canSync"
                      />
                    </v-card-text>
                  </v-card>
                </v-menu>
              </div>
            </div>

                <LatexPdfViewer
                  ref="pdfViewerRef"
                  :workspace-id="workspaceId"
                  :job-id="pdfJobId"
                  :refresh-key="pdfRefreshKey"
                  :is-compiling="isCompiling"
                  @pdf-click="handlePdfClick"
                  @no-pdf="handleNoPdf"
                />

                <div class="comments-panel">
                  <div class="comments-header">
                    <div class="d-flex align-center ga-2">
                      <LIcon size="18">mdi-comment-multiple-outline</LIcon>
                      <span class="text-body-2">{{ $t('latexCollab.comments.title') }}</span>
                    </div>
                    <v-spacer />
                    <LBtn
                      variant="text"
                      size="small"
                      prepend-icon="mdi-comment-plus-outline"
                      :disabled="!canComment"
                      :title="$t('latexCollab.comments.add')"
                      @click="openCommentDialog"
                    >
                      {{ $t('latexCollab.comments.addLabel') }}
                    </LBtn>
                  </div>

                  <v-alert v-if="commentError" type="error" variant="tonal" density="compact" class="mb-2">
                    {{ commentError }}
                  </v-alert>

                  <div v-if="comments.length === 0" class="comments-empty">
                    {{ $t('latexCollab.comments.empty') }}
                  </div>

                  <div v-else class="comment-list">
                    <div
                      v-for="c in comments"
                      :key="c.id"
                      class="comment-item"
                      :class="{ active: c.id === activeCommentId }"
                      @click="selectComment(c)"
                    >
                      <div class="comment-meta">
                        <span class="comment-author">{{ c.author_username }}</span>
                        <span class="comment-date">{{ formatDate(c.created_at) }}</span>
                      </div>
                      <div class="comment-body">{{ c.body }}</div>
                      <div class="comment-actions">
                        <LTag v-if="c.resolved_at" variant="success" size="x-small">{{ $t('latexCollab.comments.resolved') }}</LTag>
                        <v-btn
                          icon
                          variant="text"
                          size="x-small"
                          :title="c.resolved_at ? $t('latexCollab.comments.reopen') : $t('latexCollab.comments.resolve')"
                          @click.stop="toggleCommentResolved(c)"
                        >
                          <LIcon size="16">mdi-check</LIcon>
                        </v-btn>
                        <v-btn
                          icon
                          variant="text"
                          size="x-small"
                          :title="$t('common.delete')"
                          @click.stop="deleteComment(c)"
                        >
                          <LIcon size="16">mdi-delete-outline</LIcon>
                        </v-btn>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </template>
      </div>
    </div>

    <!-- Share / Members Dialog -->
    <ShareDialog
      v-model="shareDialog"
      :workspace-name="workspace?.name"
      :owner-info="ownerInfo"
      :members="members"
      :excluded-usernames="excludedUsernames"
      :loading="membersLoading"
      :error="shareError"
      :removing-username="removingUsername"
      :can-remove="canShareWorkspace"
      @invite="inviteMember"
      @remove="removeMember"
    />

    <!-- Git Detail Dialog -->
    <GitDetailDialog
      v-model="gitDetailDialog"
      :workspace-id="workspaceId"
      :selected-document-id="selectedNodeId"
      :can-commit="hasPermission('feature:latex_collab:edit')"
      :get-content="getEditorContent"
      :before-commit="handleBeforeCommit"
      :before-rollback="handleBeforeRollback"
      @committed="refreshCommits"
      @rollback="handleRollback"
      @restored="handleRestored"
    />

    <v-dialog v-model="commentDialog" max-width="520">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon class="mr-2">mdi-comment-plus-outline</LIcon>
          {{ $t('latexCollab.comments.dialog.title') }}
          <v-spacer />
          <LIconBtn icon="mdi-close" :tooltip="$t('common.close')" @click="commentDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-alert v-if="commentError" type="error" variant="tonal" class="mb-3" density="compact">
            {{ commentError }}
          </v-alert>
          <v-textarea
            v-model="commentDraft"
            :label="$t('latexCollab.comments.dialog.label')"
            variant="outlined"
            density="comfortable"
            auto-grow
            hide-details
          />
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" :title="$t('latexCollab.comments.dialog.cancelTitle')" @click="commentDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" :title="$t('latexCollab.comments.dialog.saveTitle')" :disabled="!canSubmitComment" @click="submitComment">
            {{ $t('common.save') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Compile Log Dialog -->
    <CompileLogDialog
      v-model="compileLogDialog"
      :error="compileError"
      :issues="compileIssues"
      :log="compileLog"
      @jump-to-issue="jumpToIssue"
    />

    <!-- Zotero Dialog -->
    <v-dialog v-model="zoteroDialog" max-width="600">
      <v-card class="zotero-dialog">
        <v-card-title class="d-flex align-center">
          <LIcon class="mr-2">zotero</LIcon>
          <div>
            <div>{{ $t('latexCollab.zotero.title') }}</div>
            <div class="text-caption text-medium-emphasis">{{ workspace?.name }}</div>
          </div>
          <v-spacer />
          <LIconBtn icon="mdi-close" :tooltip="$t('common.close')" size="small" @click="zoteroDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-0">
          <ZoteroPanel
            v-if="zoteroDialog && workspaceId"
            :workspace-id="workspaceId"
            @library-added="handleZoteroLibraryAdded"
            @library-synced="handleZoteroLibrarySynced"
            @library-removed="handleZoteroLibraryRemoved"
          />
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { useI18n } from 'vue-i18n'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { usePermissions } from '@/composables/usePermissions'
import { useMobile } from '@/composables/useMobile'
import { useSplitPaneResize } from '@/composables/useSplitPaneResize'
import { useWorkspaceSocket } from '@/components/MarkdownCollab/composables/useWorkspaceSocket'
import { useActiveDuration, useVisibilityTracker, useScrollDepth } from '@/composables/useAnalyticsMetrics'
import MarkdownTreePanel from '@/components/MarkdownCollab/MarkdownTreePanel.vue'
import LatexEditorPane from '@/components/LatexCollab/LatexEditorPane.vue'
import LatexPdfViewer from '@/components/LatexCollab/LatexPdfViewer.vue'
import GitDetailDialog from '@/components/LatexCollab/Git/GitDetailDialog.vue'
import ZoteroPanel from '@/components/LatexCollab/Zotero/ZoteroPanel.vue'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'
import { getAvatarUrl, formatDisplayName, formatRelativeDate } from '@/utils/userUtils'
import { getSocket } from '@/services/socketService'

// Local composables - now actually used!
import {
  useLatexCompile,
  useLatexComments,
  useLatexOutline,
  useLatexSync,
  useLatexMembers
} from './composables'

// Local components
import {
  LatexTreePanel,
  LatexContentHeader,
  ShareDialog,
  CompileLogDialog
} from './components'

// Props for customizable base path (used by AI wrapper)
const props = defineProps({
  basePath: {
    type: String,
    default: '/LatexCollab'
  },
  aiEnabled: {
    type: Boolean,
    default: false
  },
  ghostTextEnabled: {
    type: Boolean,
    default: false
  },
  ghostTextDelay: {
    type: Number,
    default: 800
  }
})

// Emits for parent communication (used by AI wrapper)
const emit = defineEmits(['document-change', 'ai-command', 'ai-action', 'request-completion', 'update:ghostTextEnabled'])

const route = useRoute()
const router = useRouter()
const { locale } = useI18n()

// Computed route base for navigation
const routeBase = computed(() => props.basePath)

const { hasPermission, fetchPermissions, username: currentUsername, isAdmin } = usePermissions()
const { isLoading, withLoading, setLoading } = useSkeletonLoading(['tree', 'document'])
const { isMobile, isTablet } = useMobile()

// Mobile sidebar state
const mobileSidebarOpen = ref(false)

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080'
const VIEWMODE_KEY = 'latex-collab-view-mode'
const TREE_COLLAPSED_KEY = 'latex-collab-tree-collapsed'
const TREE_WIDTH_KEY = 'latex-collab-tree-width'
const PANES_WIDTH_KEY = 'latex-collab-panes-width'
const OUTLINE_COLLAPSED_KEY = 'latex-outline-collapsed'
const AUTO_COMPILE_KEY = 'latex-collab-auto-compile'
const AUTO_COMPILE_DELAY_KEY = 'latex-collab-auto-compile-delay'
const SYNC_KEY = 'latex-collab-sync-enabled'

const workspace = ref(null)
const nodesFlat = ref([])

const currentText = ref('')
const gitSummary = ref({ users: [], totalChangedLines: 0 })
const editorRef = ref(null)
const pdfViewerRef = ref(null)
const pendingDocId = ref(null)
const pendingJump = ref(null)

// Panel states
const treeCollapsed = ref(localStorage.getItem(TREE_COLLAPSED_KEY) === 'true')
const treePanelWidth = ref(parseInt(localStorage.getItem(TREE_WIDTH_KEY)) || 280)
const viewMode = ref(localStorage.getItem(VIEWMODE_KEY) || 'split')
const resizingTree = ref(false)

// Panel collapse states (for unified tree stack panels)
const FILES_COLLAPSED_KEY = 'latex-collab-files-collapsed'
const GIT_COLLAPSED_KEY = 'latex-collab-git-collapsed'
const filesCollapsed = ref(localStorage.getItem(FILES_COLLAPSED_KEY) === 'true')
const gitCollapsed = ref(localStorage.getItem(GIT_COLLAPSED_KEY) === 'true')
const gitDetailDialog = ref(false)
// Outline state - initialized later via useLatexOutline composable after selectedNode is available
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

// Sharing / members - using composable
// Note: We'll initialize useLatexMembers after workspaceId, workspace, hasPermission are available

const reviewMode = ref(false)

// Compile and sync state - initialized later via composables after selectedNode is available

// Comments state - initialized later via useLatexComments composable after selectedNode is available

// Zotero dialog
const zoteroDialog = ref(false)

const assetInputRef = ref(null)

// Analytics: entity dimension for this workspace/document
const workspaceEntity = computed(() => `ws:${workspaceId.value}`)
const documentEntity = computed(() => selectedNodeId.value ? `doc:${selectedNodeId.value}` : '')

// Session active time tracking
useActiveDuration({
  category: 'latex',
  action: 'session_active_ms',
  name: () => workspaceEntity.value,
  dimensions: () => ({ entity: workspaceEntity.value, view: viewMode.value })
})

// Pane visibility tracking (editor, preview)
const paneVisibility = useVisibilityTracker({
  category: 'latex',
  action: 'pane_visible_ms',
  nameBuilder: (id) => `pane:${id}`,
  dimensions: () => ({ entity: documentEntity.value })
})

// Scroll depth for panes container
useScrollDepth(panesContainerRef, {
  category: 'latex',
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

watch(filesCollapsed, (val) => {
  localStorage.setItem(FILES_COLLAPSED_KEY, val.toString())
})

watch(gitCollapsed, (val) => {
  localStorage.setItem(GIT_COLLAPSED_KEY, val.toString())
})

// outlineCollapsed watcher is now handled by useLatexOutline composable
// autoCompileEnabled, autoCompileDelay watchers are now handled by useLatexCompile composable
// syncEnabled watcher is now handled by useLatexSync composable

watch(isMobile, (val) => {
  if (!val) {
    viewMode.value = 'split'
  }
})

watch(
  () => workspace.value?.latest_compile_job_id,
  (jobId) => {
    if (jobId) {
      loadCompileStatus(jobId)
    }
  }
)

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
    // Git panel updates are now handled by useGitStatus composable via socket events
  },
  onNodeRenamed: (data) => {
    // Update the node title in the tree
    const node = nodesFlat.value.find(n => n.id === data.nodeId)
    if (node) {
      node.title = data.newTitle
      nodesFlat.value = [...nodesFlat.value]
    }
    // Git panel updates are now handled by useGitStatus composable via socket events
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
      router.push(`${routeBase.value}/workspace/${workspaceId.value}`)
    }
    // Git panel updates are now handled by useGitStatus composable via socket events
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

// Compile status socket for real-time compile updates
let compileSocket = null
let compileSocketConnectHandler = null

function setupCompileSocket() {
  compileSocket = getSocket()
  if (!compileSocket) return

  // Handler for compile status updates
  const onCompileStatus = (data) => {
    if (data?.workspace_id !== workspaceId.value) return
    handleCompileStatusUpdate(data)
  }

  compileSocket.on('latex_collab:compile_status', onCompileStatus)

  // Subscribe to workspace updates when connected
  compileSocketConnectHandler = () => {
    compileSocket.emit('latex_collab:subscribe_workspace', { workspace_id: workspaceId.value })
  }

  if (compileSocket.connected) {
    compileSocketConnectHandler()
  }
  compileSocket.on('connect', compileSocketConnectHandler)
}

function cleanupCompileSocket() {
  if (!compileSocket) return
  compileSocket.off('latex_collab:compile_status')
  if (compileSocketConnectHandler) {
    compileSocket.off('connect', compileSocketConnectHandler)
  }
  if (workspaceId.value) {
    compileSocket.emit('latex_collab:unsubscribe_workspace', { workspace_id: workspaceId.value })
  }
  compileSocket = null
  compileSocketConnectHandler = null
}

const selectedNodeId = computed(() => routeDocId.value)
const selectedNode = computed(() => {
  if (!selectedNodeId.value) return null
  return nodesFlat.value.find(n => n.id === selectedNodeId.value) || null
})

// ============================================================
// COMPOSABLES INTEGRATION
// ============================================================

// Members management composable
const {
  shareDialog,
  members,
  membersLoading,
  shareError,
  removingUsername,
  ownerInfo,
  canShareWorkspace,
  excludedUsernames,
  loadMembers,
  openShareDialog,
  inviteMember,
  removeMember
} = useLatexMembers({
  workspaceId,
  workspace,
  hasPermission,
  currentUsername,
  isAdmin
})

// Outline management composable
const {
  outlineCollapsed,
  outlineItems,
  outlineCollapsedIds,
  outlineFlatItems,
  outlineEmptyLabel,
  toggleOutlineCollapsed,
  isOutlineItemCollapsed,
  toggleOutlineItem,
  scheduleOutlineUpdate,
  jumpToOutlineItem,
  resetOutline
} = useLatexOutline({
  selectedNode,
  editorRef
})

// Comments management composable
const {
  comments,
  activeCommentId,
  commentDialog,
  commentDraft,
  commentError,
  pendingCommentRange,
  canComment,
  canSubmitComment,
  loadComments,
  openCommentDialog,
  submitComment,
  toggleCommentResolved,
  deleteComment,
  selectComment,
  resetComments
} = useLatexComments({
  selectedNode,
  editorRef,
  hasPermission
})

// Compile management composable
const {
  compileJobId,
  compileStatus,
  compileError,
  compileLog,
  compileHasPdf,
  compileHasSynctex,
  compileLogDialog,
  pdfRefreshKey,
  compileCommitId,
  compileCommitOptions,
  compileIssues,
  autoCompileEnabled,
  autoCompileDelay,
  canCompile,
  isCompiling,
  compileStatusLabel,
  compileStatusColor,
  canSync,
  pdfJobId,
  loadCompileStatus,
  loadCommitOptions,
  scheduleAutoCompile,
  triggerCompile,
  handleCompileStatusUpdate
} = useLatexCompile({
  workspaceId,
  selectedNode,
  editorRef,
  resolveDocumentIdFromPath,
  normalizePath,
  reviewMode,
  hasPermission
})

// Sync management composable
const {
  syncEnabled,
  handleEditorSyncRequest,
  handlePdfClick
} = useLatexSync({
  selectedNode,
  pdfViewerRef,
  compileJobId,
  canSync,
  jumpToDocument
})

const editorReadonly = computed(() => {
  // Read-only if user lacks edit permission, in review mode, or document is Zotero-managed
  if (!hasPermission('feature:latex_collab:edit')) return true
  if (reviewMode.value) return true
  if (selectedNode.value?.is_zotero_managed) return true
  return false
})

const canSetMainDocument = computed(() => {
  return !!(selectedNode.value && selectedNode.value.type === 'file' && !selectedNode.value.asset_id && hasPermission('feature:latex_collab:edit'))
})

// canCompile, canSync, pdfJobId, isCompiling, compileStatusLabel, compileStatusColor
// now provided by useLatexCompile composable

// canComment and canSubmitComment now provided by useLatexComments composable

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

// Outline functions now provided by useLatexOutline composable

// Auto-compile when no PDF exists
let autoCompileTriggered = false
function handleNoPdf() {
  // Prevent multiple auto-compile attempts per session
  if (autoCompileTriggered) return
  // Only auto-compile if not already compiling and user has permission
  if (!isCompiling.value && canCompile.value) {
    autoCompileTriggered = true
    triggerCompile()
  } else if (!isCompiling.value && hasPermission('feature:latex_collab:edit')) {
    // If no document selected yet, schedule retry after short delay
    setTimeout(() => {
      if (!autoCompileTriggered && !isCompiling.value && canCompile.value) {
        autoCompileTriggered = true
        triggerCompile()
      }
    }, 500)
  }
}

// Initialize pane width on mount
onMounted(async () => {
  await fetchPermissions()
  await loadTree()

  // Connect to workspace socket for real-time tree updates
  wsConnect()

  // Connect to compile status socket for real-time compile updates
  setupCompileSocket()

  // Auto-select first file if none selected
  if (!routeDocId.value) {
    const preferred = nodesFlat.value.find(n => n.id === workspace.value?.main_document_id && n.type === 'file' && !n.asset_id)
      || nodesFlat.value.find(n => n.type === 'file' && !n.asset_id)
    if (preferred) router.replace(`${routeBase.value}/workspace/${workspaceId.value}/document/${preferred.id}`)
  }

  if (!isMobile.value) {
    viewMode.value = 'split'
  }

  if (workspace.value?.latest_compile_job_id) {
    await loadCompileStatus(workspace.value.latest_compile_job_id)
  }

  // Editor pane width is now handled by CSS (flex: 1 1 50%) by default
  // Only apply saved width from localStorage when user has manually resized
})

onUnmounted(() => {
  document.removeEventListener('mousemove', onTreeMouseMove)
  document.removeEventListener('mouseup', stopTreeResize)
  // Cleanup compile status socket
  cleanupCompileSocket()
  // Timer cleanups are now handled by composables:
  // - autoCompileTimer, compilePollTimer by useLatexCompile
  // - syncTimer by useLatexSync
  // - outlineUpdateTimer by useLatexOutline
  // - Git panel refresh is now handled by useGitStatus composable in GitStatusWidget
})

function onEditorContentChange(text) {
  currentText.value = text
  if (pendingDocId.value && pendingDocId.value === selectedNodeId.value) {
    setLoading('document', false)
    pendingDocId.value = null
  }
  scheduleOutlineUpdate(text)
  scheduleAutoCompile()
  // Git panel is updated via WebSocket 'document_saved' events (see handleDocumentSaved)
  // No need for polling-based refresh here
  // Emit for AI wrapper component
  emit('document-change', text)
}

/**
 * Handle document_saved events from YJS server for real-time Git panel updates.
 *
 * This function is the final step in the real-time update chain:
 *   1. User types in editor → Yjs local update
 *   2. Yjs syncs to server → 2s debounce timer starts
 *   3. After 2s inactivity → YJS server saves to DB
 *   4. Server broadcasts `document_saved` to workspace room
 *   5. useYjsCollaboration receives event → calls onDocumentSaved callback
 *   6. EditorPane emits 'document-saved' event to parent
 *   7. This function receives the event and refreshes Git panel
 *
 * The workspace-level check ensures we only refresh for documents in THIS
 * workspace, not unrelated workspaces the user might have open in other tabs.
 *
 * @param {Object} data - Event payload from YJS server
 * @param {number} data.documentId - The document that was saved
 * @param {number} data.workspaceId - Workspace containing the document
 * @param {string} data.kind - Document type ('latex')
 * @param {number} data.contentLength - Length of saved content
 * @param {string} data.savedAt - ISO timestamp of save
 */
function handleDocumentSaved(data) {
  console.log('[LatexCollabWorkspace] document_saved empfangen:', data)
  // Git panel updates are now handled by useGitStatus composable via socket events
  // The composable automatically listens for 'latex_collab:commit_created' events
}

/**
 * Handle document_updated events from YJS server.
 * Note: Server no longer sends diff data - clients calculate diff locally.
 *
 * @param {Object} data - Event payload from YJS server
 * @param {number} data.documentId - Updated document ID
 * @param {number} data.workspaceId - Workspace containing the document
 * @param {string} data.kind - Document type ('latex')
 * @param {number} data.timestamp - Event timestamp
 */
function handleDocumentUpdated(data) {
  // Server event is now lightweight - local diff is handled by handleDiffCalculated
  // This event can be used for other purposes like activity indicators
}

/**
 * Handle local diff calculation from LatexEditorPane for INSTANT Git panel updates.
 *
 * This is called on every YJS update with diff calculated locally against
 * the baseline stored in the YJS document. No server roundtrip required.
 *
 * @param {Object} data - Diff data from local calculation
 * @param {number} data.documentId - Document ID
 * @param {number} data.insertions - Characters inserted since baseline
 * @param {number} data.deletions - Characters deleted since baseline
 * @param {boolean} data.hasChanges - Whether document differs from baseline
 */
function handleDiffCalculated(data) {
  // Real-time diff updates are now handled by the GitStatusWidget's useGitStatus composable
  // which listens to socket events directly. This function is kept for potential future use.
  if (!data.documentId) return
  console.log('[LatexCollabWorkspace] Diff calculated:', data.documentId, data.insertions, data.deletions)
}

function authHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function formatDate(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString(locale.value || undefined)
  } catch {
    return iso
  }
}

// parseLatexLog and decorateIssues now in useLatexCompile composable

// Members functions now provided by useLatexMembers composable

// Zotero library event handlers
async function handleZoteroLibraryAdded(library) {
  // Refresh the file tree to show the new .bib file
  await loadTree()
}

async function handleZoteroLibrarySynced(library) {
  // Refresh the file tree to reflect updated .bib content
  await loadTree()
}

async function handleZoteroLibraryRemoved(library) {
  // The .bib file is kept but no longer synced - no tree refresh needed
  console.log('Zotero-Bibliothek entfernt:', library.library_name)
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

function normalizePath(path) {
  if (!path) return ''
  let normalized = String(path).replace(/\\/g, '/').trim()
  if (normalized.startsWith('./')) normalized = normalized.slice(2)
  return normalized.replace(/^\/+/, '')
}

const nodeById = computed(() => {
  const map = new Map()
  nodesFlat.value.forEach((n) => map.set(n.id, n))
  return map
})

function buildNodePath(nodeId, cache) {
  if (cache.has(nodeId)) return cache.get(nodeId)
  const node = nodeById.value.get(nodeId)
  if (!node) return ''
  const parentPath = node.parent_id ? buildNodePath(node.parent_id, cache) : ''
  const full = parentPath ? `${parentPath}/${node.title}` : node.title
  cache.set(nodeId, full)
  return full
}

const nodePathById = computed(() => {
  const cache = new Map()
  const map = new Map()
  nodesFlat.value.forEach((n) => {
    map.set(n.id, buildNodePath(n.id, cache))
  })
  return map
})

const nodeIdByPath = computed(() => {
  const map = new Map()
  nodePathById.value.forEach((path, id) => {
    map.set(normalizePath(path), id)
  })
  return map
})

const nodeIdByFilename = computed(() => {
  const map = new Map()
  nodePathById.value.forEach((path, id) => {
    const name = normalizePath(path).split('/').pop()
    if (name && !map.has(name)) map.set(name, id)
  })
  return map
})

function resolveDocumentIdFromPath(path) {
  const normalized = normalizePath(path)
  if (!normalized) return null
  if (nodeIdByPath.value.has(normalized)) return nodeIdByPath.value.get(normalized)
  const filename = normalized.split('/').pop()
  if (filename && nodeIdByFilename.value.has(filename)) return nodeIdByFilename.value.get(filename)
  return null
}

async function loadTree() {
  await withLoading('tree', async () => {
    const res = await axios.get(`${API_BASE}/api/latex-collab/workspaces/${workspaceId.value}/tree`, {
      headers: authHeaders()
    })
    workspace.value = res.data.workspace
    nodesFlat.value = (res.data.nodes || []).map(n => ({ ...n, type: n.type }))
  })
}

// Debounce to prevent double-click issues
let lastSelectTime = 0
let lastSelectNodeId = null

function handleSelectNode(nodeId) {
  // Prevent duplicate clicks within 100ms on the same node
  const now = Date.now()
  if (nodeId === lastSelectNodeId && now - lastSelectTime < 100) {
    console.log('[handleSelectNode] Doppelten Klick auf nodeId ignoriert:', nodeId)
    return
  }
  lastSelectTime = now
  lastSelectNodeId = nodeId

  const node = nodesFlat.value.find(n => n.id === nodeId)
  if (!node) return

  if (node.type === 'file') {
    router.push(`${routeBase.value}/workspace/${workspaceId.value}/document/${node.id}`)
    return
  }

  // Folder: keep workspace route, but don't force a document selection
  router.push(`${routeBase.value}/workspace/${workspaceId.value}`)
}

function openAssetPicker() {
  if (!hasPermission('feature:latex_collab:edit')) return
  assetInputRef.value?.click()
}

async function handleAssetFiles(event) {
  const files = Array.from(event?.target?.files || [])
  if (!files.length) return

  for (const file of files) {
    await uploadAsset(file)
  }

  if (event?.target) {
    event.target.value = ''
  }
}

async function uploadAsset(file) {
  if (!workspaceId.value || !file) return
  if (!hasPermission('feature:latex_collab:edit')) return

  const parentId = selectedNode.value?.type === 'folder'
    ? selectedNode.value.id
    : (selectedNode.value?.parent_id ?? null)

  const form = new FormData()
  form.append('file', file)
  if (parentId) form.append('parent_id', String(parentId))

  try {
    const res = await axios.post(
      `${API_BASE}/api/latex-collab/workspaces/${workspaceId.value}/assets`,
      form,
      { headers: authHeaders() }
    )
    const newNode = res.data.node
    if (newNode) {
      nodesFlat.value = [...nodesFlat.value, { ...newNode, type: newNode.type }]
      emitNodeCreated(newNode)
    }
  } catch (e) {
    console.error('Asset-Upload fehlgeschlagen:', e)
    await loadTree()
  }
}

async function handleCreateNode({ parentId, type, title }) {
  if (!hasPermission('feature:latex_collab:edit')) return
  try {
    const res = await axios.post(
      `${API_BASE}/api/latex-collab/documents`,
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
    console.error('Konnte Knoten nicht erstellen:', e)
    await loadTree() // Fallback: reload tree
  }
}

async function handleRenameNode({ id, parentId, title }) {
  if (!hasPermission('feature:latex_collab:edit')) return
  try {
    await axios.patch(
      `${API_BASE}/api/latex-collab/documents/${id}`,
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
    console.error('Konnte Knoten nicht umbenennen:', e)
    await loadTree() // Fallback: reload tree
  }
}

async function handleDeleteNode({ id }) {
  if (!hasPermission('feature:latex_collab:edit')) return
  try {
    await axios.delete(`${API_BASE}/api/latex-collab/documents/${id}`, {
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
    // Git panel updates are now handled by useGitStatus composable via socket events

    // Navigate away if viewing deleted document
    if (routeDocId.value === id) {
      router.push(`${routeBase.value}/workspace/${workspaceId.value}`)
    }
  } catch (e) {
    console.error('Konnte Knoten nicht loeschen:', e)
    await loadTree() // Fallback: reload tree
  }
}

async function handleMoveNode({ id, parentId, orderIndex }) {
  if (!hasPermission('feature:latex_collab:edit')) return
  try {
    await axios.patch(
      `${API_BASE}/api/latex-collab/documents/${id}`,
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
    console.error('Konnte Knoten nicht verschieben:', e)
    await loadTree() // Fallback: reload tree
  }
}

async function setMainDocument() {
  if (!canSetMainDocument.value || !selectedNode.value) return
  try {
    const res = await axios.patch(
      `${API_BASE}/api/latex-collab/workspaces/${workspaceId.value}/main`,
      { document_id: selectedNode.value.id },
      { headers: authHeaders() }
    )
    workspace.value = res.data.workspace || workspace.value
  } catch (e) {
    console.error('Konnte Hauptdokument nicht festlegen:', e)
  }
}

// Compile and sync functions now provided by useLatexCompile and useLatexSync composables

// Comments functions now provided by useLatexComments composable

function jumpToIssue(issue) {
  if (!issue || !issue.document_id) return
  const node = nodeById.value.get(issue.document_id)
  if (!node || node.asset_id) return
  jumpToDocument(issue.document_id, issue.line || 1, 1)
}

function jumpToDocument(documentId, line = 1, column = 1) {
  if (!documentId) return
  const node = nodeById.value.get(documentId)
  if (!node || node.asset_id) return
  if (selectedNodeId.value === documentId) {
    nextTick(() => {
      editorRef.value?.jumpToLine?.(line, column)
    })
    return
  }
  pendingJump.value = { documentId, line, column }
  router.push(`${routeBase.value}/workspace/${workspaceId.value}/document/${documentId}`)
}

// Get current content from editor for diff viewer in Git Panel
function getEditorContent() {
  return editorRef.value?.getCurrentContent?.() || ''
}

async function refreshCommits() {
  // Refresh the git baseline after commit to update diff decorations
  await editorRef.value?.refreshBaseline?.()
  editorRef.value?.clearHighlights?.()
  await loadCommitOptions()
  // Git panel updates are now handled by useGitStatus composable via socket events
}

async function handleRollback(payload) {
  const documentId = typeof payload === 'object' && payload !== null ? payload.documentId : payload
  const baseline = typeof payload === 'object' && payload !== null ? payload.baseline : null
  console.log('[handleRollback] Aufgerufen mit documentId:', documentId, 'selectedNodeId:', selectedNodeId.value)

  // Build the room name for this document
  const roomName = `latex_${documentId}`

  // If the rolled back document is currently open, use reloadRoom which:
  // 1. Destroys the local ydoc (clearing all local state/history)
  // 2. Creates a fresh ydoc
  // 3. Sends reload_room to server which clears cache and reloads from DB
  // 4. Server broadcasts snapshot_document to all clients
  // This ensures a clean slate without Yjs merge conflicts
  if (selectedNodeId.value === documentId) {
    console.log('[handleRollback] Dokument ist derzeit geoeffnet, verwende reloadRoom fuer sauberen Reset')
    const result = await editorRef.value?.reloadRoom?.()
    console.log('[handleRollback] reloadRoom Ergebnis:', result)
    // Refresh the baseline to update diff decorations
    await editorRef.value?.refreshBaseline?.()
    editorRef.value?.clearHighlights?.()
  } else {
    // If the document is NOT currently open, only invalidate the YJS server cache
    // This is necessary because the YJS server caches room state and would serve
    // stale content when the user later opens this document
    console.log('[handleRollback] Dokument ist NICHT geoeffnet, invalidiere YJS-Cache fuer Raum:', roomName)
    const cacheResult = await editorRef.value?.reloadAnyRoom?.(roomName)
    console.log('[handleRollback] reloadAnyRoom Ergebnis:', cacheResult)
  }
}

async function handleRestored(documentId) {
  console.log('[handleRestored] Datei wiederhergestellt:', documentId)
  // Refresh the tree to show the restored file
  await loadTree()
}

async function handleBeforeRollback(documentId) {
  if (documentId && selectedNodeId.value === documentId) {
    await editorRef.value?.flushDocumentState?.()
  }
}

async function handleBeforeCommit(documentIds = []) {
  if (!Array.isArray(documentIds) || documentIds.length === 0) return
  if (selectedNodeId.value && documentIds.includes(selectedNodeId.value)) {
    await editorRef.value?.flushDocumentState?.()
  }
}

// Track if this is the initial mount vs subsequent document switches
let isInitialDocumentLoad = true
watch(
  selectedNodeId,
  (docId) => {
    currentText.value = ''
    gitSummary.value = { users: [], totalChangedLines: 0, hasChanges: false, insertions: 0, deletions: 0 }
    resetOutline() // Using composable function
    if (docId) {
      // Only show loading skeleton on initial mount, not on document switches
      // Document switches are handled smoothly by the editor's YJS room switch
      if (isInitialDocumentLoad) {
        pendingDocId.value = docId
        setLoading('document', true)
        isInitialDocumentLoad = false
      }
      const node = nodesFlat.value.find(n => n.id === docId)
      if (node?.asset_id) {
        pendingDocId.value = null
        setLoading('document', false)
      }
      activeCommentId.value = null
      commentError.value = ''
      commentDraft.value = ''
      loadComments()
      loadCommitOptions()
      if (pendingJump.value && pendingJump.value.documentId === docId) {
        const { line, column } = pendingJump.value
        pendingJump.value = null
        nextTick(() => {
          editorRef.value?.jumpToLine?.(line, column)
        })
      }
    } else {
      pendingDocId.value = null
      setLoading('document', false)
      comments.value = []
      activeCommentId.value = null
      pendingCommentRange.value = null
      commentError.value = ''
      commentDraft.value = ''
      compileCommitId.value = null
      compileCommitOptions.value = [{ title: 'Aktuell', value: null }]
    }
  },
  { immediate: true }
)

watch(
  selectedNode,
  (node) => {
    if (node && node.type === 'file' && !node.asset_id) {
      loadComments()
      loadCommitOptions()
    }
  }
)
</script>

<style scoped>
/* Import extracted styles */
@import './styles/LatexCollabWorkspace.css';
</style>
