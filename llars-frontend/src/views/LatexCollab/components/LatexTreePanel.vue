<!--
  LatexTreePanel.vue

  Combined tree panel for LaTeX workspace with unified collapsible panels.
  Contains: File Tree, Git Status, Document Outline - all with consistent styling.
-->
<template>
  <!-- Mobile Navigation Drawer -->
  <v-navigation-drawer
    v-if="isMobile"
    :model-value="mobileOpen"
    @update:model-value="$emit('update:mobileOpen', $event)"
    temporary
    width="300"
    class="mobile-tree-drawer"
  >
    <div class="mobile-tree-content">
      <!-- Workspace Header (Mobile) -->
      <div class="sidebar-workspace-header">
        <v-btn icon variant="text" size="x-small" @click="$emit('navigate-back')">
          <LIcon size="16">mdi-arrow-left</LIcon>
        </v-btn>
        <span class="sidebar-workspace-name text-truncate">{{ workspaceName }}</span>
      </div>

      <!-- Files Panel (Mobile) -->
      <TreeStackPanel
        :title="$t('latexCollab.tree.files')"
        icon="mdi-file-tree"
        v-model:collapsed="localFilesCollapsed"
      >
        <template #actions>
          <v-btn icon variant="text" size="x-small" :disabled="!canEdit" @click="openCreate('file')">
            <LIcon size="16">mdi-file-plus</LIcon>
          </v-btn>
          <v-btn icon variant="text" size="x-small" :disabled="!canEdit" @click="openCreate('folder')">
            <LIcon size="16">mdi-folder-plus</LIcon>
          </v-btn>
        </template>
        <MarkdownTreePanel
          ref="treePanelMobileRef"
          :workspace-id="workspaceId"
          :nodes="nodes"
          :selected-id="selectedId"
          :loading="loading"
          :can-edit="canEdit"
          :recently-added-ids="recentlyAddedIds"
          :file-placeholder="$t('latexCollab.tree.filePlaceholder')"
          file-icon="mdi-file-code-outline"
          file-icon-color="primary"
          hide-header
          @select="handleMobileSelect"
          @create="$emit('create', $event)"
          @rename="$emit('rename', $event)"
          @remove="$emit('remove', $event)"
          @move="$emit('move', $event)"
        />
      </TreeStackPanel>

      <!-- Collabs (Mobile) -->
      <TreeStackPanel
        class="collabs-panel"
        :title="$t('latexCollab.tree.collabs')"
        icon="mdi-account-multiple"
        v-model:collapsed="localOnlineCollapsed"
        :badge="collabBadge"
        :badge-variant="pendingRequests.length > 0 ? 'warning' : 'info'"
      >
        <template #actions>
          <v-btn v-if="canShare" icon variant="text" size="x-small" @click="$emit('open-share')">
            <LIcon size="16">mdi-account-multiple-plus</LIcon>
          </v-btn>
        </template>
        <div class="online-users-list">
          <div v-for="u in collabUsers" :key="u.username" class="online-user-item">
            <div class="online-user-avatar-wrap" :class="{ online: u.isOnline }" :style="u.isOnline ? { borderColor: u.color } : {}">
              <LAvatar :username="u.username" size="xs" />
            </div>
            <span class="online-user-name text-truncate">{{ u.username }}</span>
            <LIcon v-if="u.isOwner" size="14" class="text-medium-emphasis">mdi-crown-outline</LIcon>
            <span v-if="u.isOnline" class="online-user-dot" :style="{ backgroundColor: u.color }" />
          </div>
          <!-- Pending Access Requests (Mobile) -->
          <template v-if="canShare && pendingRequests.length > 0">
            <div class="pending-requests-divider">
              <span>{{ $t('latexCollab.accessRequests.pendingRequests') }}</span>
            </div>
            <div v-for="req in pendingRequests" :key="'req-' + req.id" class="online-user-item pending-request-item">
              <div class="online-user-avatar-wrap pending">
                <LAvatar :username="req.requester_username" :seed="req.requester_avatar_seed" :src="req.requester_avatar_url" size="xs" />
              </div>
              <span class="online-user-name text-truncate">{{ req.requester_username }}</span>
              <v-btn icon variant="text" size="x-small" color="success" :title="$t('latexCollab.accessRequests.approve')" @click.stop="$emit('approve-request', req.id)">
                <LIcon size="14">mdi-check</LIcon>
              </v-btn>
              <v-btn icon variant="text" size="x-small" color="error" :title="$t('latexCollab.accessRequests.reject')" @click.stop="$emit('reject-request', req.id)">
                <LIcon size="14">mdi-close</LIcon>
              </v-btn>
            </div>
          </template>
        </div>
        <div v-if="showConnectionStatus" class="online-users-status">
          <v-chip size="x-small" variant="tonal" :color="isConnected ? 'success' : 'warning'">
            <LIcon start size="12">{{ isConnected ? 'mdi-cloud-check-outline' : 'mdi-cloud-alert-outline' }}</LIcon>
            {{ isConnected ? $t('latexCollab.header.liveSync') : $t('latexCollab.header.reconnecting') }}
          </v-chip>
          <v-chip
            v-if="aiEnabled"
            size="x-small"
            :color="ghostTextEnabled ? 'primary' : 'default'"
            :variant="ghostTextEnabled ? 'flat' : 'outlined'"
            class="cursor-pointer"
            @click="$emit('toggle-ghost-text')"
          >
            <LIcon start size="12">{{ ghostTextEnabled ? 'mdi-lightning-bolt' : 'mdi-lightning-bolt-outline' }}</LIcon>
            {{ $t('latexCollab.header.ghostText') }}
          </v-chip>
        </div>
      </TreeStackPanel>

      <!-- Git Panel (Mobile) -->
      <TreeStackPanel
        :title="$t('workspaceGit.title')"
        icon="mdi-source-branch"
        v-model:collapsed="localGitCollapsed"
        :badge="gitTotalChanges > 0 ? gitTotalChanges : null"
        badge-variant="warning"
      >
        <template #actions>
          <v-btn icon variant="text" size="x-small" @click="$emit('open-git-detail')">
            <LIcon size="16">mdi-open-in-new</LIcon>
          </v-btn>
        </template>
        <GitPanelContent
          ref="gitPanelMobileRef"
          :workspace-id="workspaceId"
          :can-commit="canCommit"
          :api-prefix="apiPrefix"
          @open-detail="$emit('open-git-detail')"
          @committed="$emit('committed')"
          @total-changes="gitTotalChanges = $event"
        />
      </TreeStackPanel>

      <!-- Outline Panel (Mobile) -->
      <TreeStackPanel
        :title="$t('latexCollab.outline.title')"
        icon="mdi-format-list-bulleted"
        v-model:collapsed="localOutlineCollapsed"
      >
        <OutlinePanelContent
          :items="outlineFlatItems"
          :empty-label="outlineEmptyLabel"
          :is-item-collapsed="isOutlineItemCollapsed"
          @toggle-item="$emit('toggle-outline-item', $event)"
          @jump-to-item="$emit('jump-to-outline-item', $event)"
        />
      </TreeStackPanel>
    </div>
    <template #append>
      <v-divider />
      <v-list density="compact" class="pa-2">
        <v-list-item prepend-icon="mdi-home" :title="$t('latexCollab.workspace.nav.home')" @click="$emit('navigate-home')" />
        <v-list-item prepend-icon="mdi-folder-multiple" :title="$t('latexCollab.workspace.nav.workspaces')" @click="$emit('navigate-workspaces')" />
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
    <!-- Collapsed State (icon bar) -->
    <div v-if="treeCollapsed" class="tree-collapsed">
      <div class="collapsed-bar" @click="$emit('update:treeCollapsed', false)">
        <div class="collapsed-icon-box">
          <LIcon size="18">mdi-file-tree</LIcon>
        </div>
        <span class="collapsed-label">{{ $t('latexCollab.tree.files') }}</span>
        <v-spacer />
        <LIcon size="18" class="expand-icon">mdi-chevron-right</LIcon>
      </div>
      <!-- Git badge when tree collapsed -->
      <div v-if="gitTotalChanges > 0" class="collapsed-git-badge" @click="$emit('open-git-detail')">
        <LIcon size="16">mdi-source-branch</LIcon>
        <span class="badge-count">{{ gitTotalChanges }}</span>
      </div>
    </div>

    <!-- Expanded State -->
    <div v-else class="tree-expanded">
      <!-- Workspace Header -->
      <div class="sidebar-workspace-header">
        <v-btn icon variant="text" size="x-small" @click="$emit('navigate-back')">
          <LIcon size="16">mdi-arrow-left</LIcon>
        </v-btn>
        <span class="sidebar-workspace-name text-truncate">{{ workspaceName }}</span>
      </div>

      <div class="tree-stack" ref="treeStackRef">
        <!-- Files Panel -->
        <TreeStackPanel
          :title="$t('latexCollab.tree.files')"
          icon="mdi-file-tree"
          v-model:collapsed="localFilesCollapsed"
          :style="getPanelStyle(0)"
        >
          <template #actions>
            <v-btn icon variant="text" size="x-small" :disabled="!canEdit" :title="$t('markdownCollab.tree.actions.newFile')" @click="openCreate('file')">
              <LIcon size="16">mdi-file-plus</LIcon>
            </v-btn>
            <v-btn icon variant="text" size="x-small" :disabled="!canEdit" :title="$t('markdownCollab.tree.actions.newFolder')" @click="openCreate('folder')">
              <LIcon size="16">mdi-folder-plus</LIcon>
            </v-btn>
            <v-btn icon variant="text" size="x-small" :title="$t('latexCollab.tree.uploadAsset')" @click.stop="$emit('open-asset-picker')">
              <LIcon size="16">mdi-paperclip</LIcon>
            </v-btn>
            <v-btn icon variant="text" size="x-small" :title="$t('latexCollab.tree.collapse')" @click.stop="$emit('update:treeCollapsed', true)">
              <LIcon size="16">mdi-chevron-left</LIcon>
            </v-btn>
          </template>
          <MarkdownTreePanel
            ref="treePanelDesktopRef"
            :workspace-id="workspaceId"
            :nodes="nodes"
            :selected-id="selectedId"
            :loading="loading"
            :can-edit="canEdit"
            :recently-added-ids="recentlyAddedIds"
            :file-placeholder="$t('latexCollab.tree.filePlaceholder')"
            file-icon="mdi-file-code-outline"
            file-icon-color="primary"
            hide-header
            @select="$emit('select', $event)"
            @create="$emit('create', $event)"
            @rename="$emit('rename', $event)"
            @remove="$emit('remove', $event)"
            @move="$emit('move', $event)"
          />
        </TreeStackPanel>

        <!-- Resize Divider: Files | Collabs -->
        <PanelResizeDivider
          @resize-start="startPanelResize(0, $event)"
          @resize-move="onPanelResize"
          @resize-end="endPanelResize"
        />

        <!-- Collabs -->
        <TreeStackPanel
          :title="$t('latexCollab.tree.collabs')"
          icon="mdi-account-multiple"
          v-model:collapsed="localOnlineCollapsed"
          :badge="collabBadge"
          :badge-variant="pendingRequests.length > 0 ? 'warning' : 'info'"
          :style="getPanelStyle(1)"
        >
          <template #actions>
            <v-btn v-if="canShare" icon variant="text" size="x-small" :title="$t('latexCollab.share.title')" @click="$emit('open-share')">
              <LIcon size="16">mdi-account-multiple-plus</LIcon>
            </v-btn>
          </template>
          <div class="online-users-list">
            <div v-for="u in collabUsers" :key="u.username" class="online-user-item">
              <div class="online-user-avatar-wrap" :class="{ online: u.isOnline }" :style="u.isOnline ? { borderColor: u.color } : {}">
                <LAvatar :username="u.username" size="xs" />
              </div>
              <span class="online-user-name text-truncate">{{ u.username }}</span>
              <LIcon v-if="u.isOwner" size="14" class="text-medium-emphasis">mdi-crown-outline</LIcon>
              <span v-if="u.isOnline" class="online-user-dot" :style="{ backgroundColor: u.color }" />
            </div>
            <!-- Pending Access Requests (owner only) -->
            <template v-if="canShare && pendingRequests.length > 0">
              <div class="pending-requests-divider">
                <span>{{ $t('latexCollab.accessRequests.pendingRequests') }}</span>
              </div>
              <div v-for="req in pendingRequests" :key="'req-' + req.id" class="online-user-item pending-request-item">
                <div class="online-user-avatar-wrap pending">
                  <LAvatar :username="req.requester_username" :seed="req.requester_avatar_seed" :src="req.requester_avatar_url" size="xs" />
                </div>
                <span class="online-user-name text-truncate">{{ req.requester_username }}</span>
                <v-btn icon variant="text" size="x-small" color="success" :title="$t('latexCollab.accessRequests.approve')" @click.stop="$emit('approve-request', req.id)">
                  <LIcon size="14">mdi-check</LIcon>
                </v-btn>
                <v-btn icon variant="text" size="x-small" color="error" :title="$t('latexCollab.accessRequests.reject')" @click.stop="$emit('reject-request', req.id)">
                  <LIcon size="14">mdi-close</LIcon>
                </v-btn>
              </div>
            </template>
          </div>
          <div v-if="showConnectionStatus" class="online-users-status">
            <v-chip size="x-small" variant="tonal" :color="isConnected ? 'success' : 'warning'">
              <LIcon start size="12">{{ isConnected ? 'mdi-cloud-check-outline' : 'mdi-cloud-alert-outline' }}</LIcon>
              {{ isConnected ? $t('latexCollab.header.liveSync') : $t('latexCollab.header.reconnecting') }}
            </v-chip>
            <v-chip
              v-if="aiEnabled"
              size="x-small"
              :color="ghostTextEnabled ? 'primary' : 'default'"
              :variant="ghostTextEnabled ? 'flat' : 'outlined'"
              class="cursor-pointer"
              @click="$emit('toggle-ghost-text')"
            >
              <LIcon start size="12">{{ ghostTextEnabled ? 'mdi-lightning-bolt' : 'mdi-lightning-bolt-outline' }}</LIcon>
              {{ $t('latexCollab.header.ghostText') }}
            </v-chip>
          </div>
        </TreeStackPanel>

        <!-- Resize Divider: Collabs | Git -->
        <PanelResizeDivider
          @resize-start="startPanelResize(1, $event)"
          @resize-move="onPanelResize"
          @resize-end="endPanelResize"
        />

        <!-- Git Panel -->
        <TreeStackPanel
          :title="$t('workspaceGit.title')"
          icon="mdi-source-branch"
          v-model:collapsed="localGitCollapsed"
          :badge="gitTotalChanges > 0 ? gitTotalChanges : null"
          badge-variant="warning"
          :style="getPanelStyle(2)"
        >
          <template #actions>
            <v-btn icon variant="text" size="x-small" :title="$t('workspaceGit.openDetail')" @click="$emit('open-git-detail')">
              <LIcon size="16">mdi-open-in-new</LIcon>
            </v-btn>
          </template>
          <GitPanelContent
            ref="gitPanelDesktopRef"
            :workspace-id="workspaceId"
            :can-commit="canCommit"
            :api-prefix="apiPrefix"
            @open-detail="$emit('open-git-detail')"
            @committed="$emit('committed')"
            @total-changes="gitTotalChanges = $event"
          />
        </TreeStackPanel>

        <!-- Resize Divider: Git | Outline -->
        <PanelResizeDivider
          @resize-start="startPanelResize(2, $event)"
          @resize-move="onPanelResize"
          @resize-end="endPanelResize"
        />

        <!-- Outline Panel -->
        <TreeStackPanel
          :title="$t('latexCollab.outline.title')"
          icon="mdi-format-list-bulleted"
          v-model:collapsed="localOutlineCollapsed"
          :style="getPanelStyle(3)"
        >
          <OutlinePanelContent
            :items="outlineFlatItems"
            :empty-label="outlineEmptyLabel"
            :is-item-collapsed="isOutlineItemCollapsed"
            @toggle-item="$emit('toggle-outline-item', $event)"
            @jump-to-item="$emit('jump-to-outline-item', $event)"
          />
        </TreeStackPanel>
      </div>
    </div>
  </div>

</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import MarkdownTreePanel from '@/components/MarkdownCollab/MarkdownTreePanel.vue'
import TreeStackPanel from './TreeStackPanel.vue'
import PanelResizeDivider from './PanelResizeDivider.vue'
import GitPanelContent from './GitPanelContent.vue'
import OutlinePanelContent from './OutlinePanelContent.vue'

const STORAGE_KEY = 'latex-tree-panel-heights'

const props = defineProps({
  isMobile: { type: Boolean, default: false },
  mobileOpen: { type: Boolean, default: false },
  workspaceId: { type: Number, required: true },
  nodes: { type: Array, default: () => [] },
  selectedId: { type: Number, default: null },
  loading: { type: Boolean, default: false },
  canEdit: { type: Boolean, default: false },
  recentlyAddedIds: { type: Set, default: () => new Set() },
  treeCollapsed: { type: Boolean, default: false },
  treePanelWidth: { type: Number, default: 280 },
  outlineFlatItems: { type: Array, default: () => [] },
  outlineEmptyLabel: { type: String, default: '' },
  isOutlineItemCollapsed: { type: Function, default: () => false },
  // Git props
  canCommit: { type: Boolean, default: false },
  apiPrefix: { type: String, default: '/api/latex-collab' },
  // Online users & members
  activeUsers: { type: Array, default: () => [] },
  members: { type: Array, default: () => [] },
  ownerInfo: { type: Object, default: () => ({}) },
  canShare: { type: Boolean, default: false },
  pendingRequests: { type: Array, default: () => [] },
  // Workspace header
  workspaceName: { type: String, default: '' },
  // Connection status
  isConnected: { type: Boolean, default: false },
  aiEnabled: { type: Boolean, default: false },
  ghostTextEnabled: { type: Boolean, default: false },
  showConnectionStatus: { type: Boolean, default: false },
  // Collapse states (optional external control)
  filesCollapsed: { type: Boolean, default: false },
  gitCollapsed: { type: Boolean, default: true },
  onlineCollapsed: { type: Boolean, default: false },
  outlineCollapsed: { type: Boolean, default: false }
})

const emit = defineEmits([
  'update:mobileOpen',
  'update:treeCollapsed',
  'update:filesCollapsed',
  'update:gitCollapsed',
  'update:onlineCollapsed',
  'update:outlineCollapsed',
  'select',
  'create',
  'rename',
  'remove',
  'move',
  'open-asset-picker',
  'navigate-home',
  'navigate-workspaces',
  'navigate-back',
  'toggle-outline-item',
  'jump-to-outline-item',
  'open-git-detail',
  'committed',
  'toggle-ghost-text',
  'open-share',
  'approve-request',
  'reject-request'
])

// Local collapse states with two-way binding
const localFilesCollapsed = computed({
  get: () => props.filesCollapsed,
  set: (val) => emit('update:filesCollapsed', val)
})

const localGitCollapsed = computed({
  get: () => props.gitCollapsed,
  set: (val) => emit('update:gitCollapsed', val)
})

const localOnlineCollapsed = computed({
  get: () => props.onlineCollapsed,
  set: (val) => emit('update:onlineCollapsed', val)
})

const localOutlineCollapsed = computed({
  get: () => props.outlineCollapsed,
  set: (val) => emit('update:outlineCollapsed', val)
})

// Collabs: merge activeUsers + members + owner into one list
const collabUsers = computed(() => {
  const onlineMap = new Map()
  for (const u of props.activeUsers) {
    onlineMap.set(u.username, u.color)
  }

  const seen = new Set()
  const users = []
  const ownerName = props.ownerInfo?.username || ''

  function addUser(username, isOwner = false) {
    if (!username || seen.has(username)) return
    seen.add(username)
    const color = onlineMap.get(username) || null
    users.push({ username, isOnline: !!color, color, isOwner })
  }

  // 1. Owner
  if (ownerName) addUser(ownerName, true)

  // 2. Active users (currently editing — always visible)
  for (const u of props.activeUsers) {
    addUser(u.username, u.username === ownerName)
  }

  // 3. Invited members (offline ones too)
  for (const m of props.members) {
    addUser(m.username, m.username === ownerName)
  }

  // Sort: online first, owner always top
  users.sort((a, b) => {
    if (a.isOwner && !b.isOwner) return -1
    if (!a.isOwner && b.isOwner) return 1
    if (a.isOnline && !b.isOnline) return -1
    if (!a.isOnline && b.isOnline) return 1
    return 0
  })

  return users
})

// Badge for COLLABS panel: shows pending request count or user count
const collabBadge = computed(() => {
  if (props.pendingRequests.length > 0) return props.pendingRequests.length
  if (collabUsers.value.length > 0) return collabUsers.value.length
  return null
})

// Git changes badge
const gitTotalChanges = ref(0)

// Tree panel refs for dialog access
const treePanelMobileRef = ref(null)
const treePanelDesktopRef = ref(null)

// Git panel refs for external refresh
const gitPanelMobileRef = ref(null)
const gitPanelDesktopRef = ref(null)

/**
 * Open the create dialog in MarkdownTreePanel
 */
function openCreate(type) {
  treePanelMobileRef.value?.openCreateDialog?.(type)
  treePanelDesktopRef.value?.openCreateDialog?.(type)
}

/**
 * Refresh the Git panel from external trigger
 */
function refreshGit() {
  gitPanelMobileRef.value?.refresh?.()
  gitPanelDesktopRef.value?.refresh?.()
}

// Panel heights for resize (flex proportions for each panel)
// Order: [Files, Collabs, Git, Outline]
const PANEL_COUNT = 4
const DEFAULT_HEIGHTS = [35, 15, 25, 25]

const treeStackRef = ref(null)
const panelHeights = ref([...DEFAULT_HEIGHTS])
const resizingAboveIndex = ref(-1)
const resizingBelowIndex = ref(-1)
const resizeStartY = ref(0)
const resizeStartHeights = ref([])

// Load saved heights
onMounted(() => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      if (Array.isArray(parsed) && parsed.length === PANEL_COUNT) {
        panelHeights.value = parsed
      }
    }
  } catch {}
})

function saveHeights() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(panelHeights.value))
  } catch {}
}

function getPanelStyle(index) {
  // Only apply flex-basis when panel is expanded
  const collapsed = [localFilesCollapsed.value, localOnlineCollapsed.value, localGitCollapsed.value, localOutlineCollapsed.value]
  if (collapsed[index]) return {}

  // Count expanded panels
  const expandedCount = collapsed.filter(c => !c).length
  if (expandedCount <= 1) return { flex: '1' }

  return {
    flex: `${panelHeights.value[index]} 1 0`,
    minHeight: '60px'
  }
}

function findExpandedPanel(startIndex, direction) {
  const collapsed = [localFilesCollapsed.value, localOnlineCollapsed.value, localGitCollapsed.value, localOutlineCollapsed.value]
  const step = direction === 'up' ? -1 : 1
  for (let i = startIndex; i >= 0 && i < PANEL_COUNT; i += step) {
    if (!collapsed[i]) return i
  }
  return -1
}

function startPanelResize(dividerPosition, event) {
  // Find nearest expanded panel above (at or before dividerPosition)
  resizingAboveIndex.value = findExpandedPanel(dividerPosition, 'up')
  // Find nearest expanded panel below (at or after dividerPosition+1)
  resizingBelowIndex.value = findExpandedPanel(dividerPosition + 1, 'down')
  resizeStartY.value = event.y
  resizeStartHeights.value = [...panelHeights.value]
}

function onPanelResize(event) {
  if (resizingAboveIndex.value < 0 || resizingBelowIndex.value < 0 || !treeStackRef.value) return

  const containerHeight = treeStackRef.value.clientHeight
  const deltaPercent = (event.deltaY / containerHeight) * 100

  const newHeights = [...resizeStartHeights.value]
  newHeights[resizingAboveIndex.value] = Math.max(5, resizeStartHeights.value[resizingAboveIndex.value] + deltaPercent)
  newHeights[resizingBelowIndex.value] = Math.max(5, resizeStartHeights.value[resizingBelowIndex.value] - deltaPercent)

  panelHeights.value = newHeights
}

function endPanelResize() {
  resizingAboveIndex.value = -1
  resizingBelowIndex.value = -1
  saveHeights()
}

/**
 * When a panel expands/collapses, redistribute space so that panels
 * ABOVE the toggled panel keep their size (header stays in place).
 * Space is taken from / given to panels BELOW.
 */
function handlePanelToggle(index, nowCollapsed) {
  const collapsed = [localFilesCollapsed.value, localOnlineCollapsed.value, localGitCollapsed.value, localOutlineCollapsed.value]
  const newHeights = [...panelHeights.value]

  // Find expanded panels below and above (excluding the toggled panel)
  const belowExpanded = []
  for (let i = index + 1; i < PANEL_COUNT; i++) {
    if (!collapsed[i]) belowExpanded.push(i)
  }
  const aboveExpanded = []
  for (let i = 0; i < index; i++) {
    if (!collapsed[i]) aboveExpanded.push(i)
  }

  if (nowCollapsed) {
    // Panel collapsed — give its freed space to panels below
    const freed = newHeights[index]
    const targets = belowExpanded.length > 0 ? belowExpanded : aboveExpanded
    if (targets.length > 0) {
      const total = targets.reduce((s, i) => s + newHeights[i], 0)
      for (const i of targets) {
        newHeights[i] += freed * (total > 0 ? newHeights[i] / total : 1 / targets.length)
      }
    }
  } else {
    // Panel expanded — take space from panels below so header stays put
    // Use the panel's last known height (preserved from before collapse) or default
    const needed = newHeights[index] > 0 ? newHeights[index] : DEFAULT_HEIGHTS[index]
    const donors = belowExpanded.length > 0 ? belowExpanded : aboveExpanded
    if (donors.length > 0) {
      const total = donors.reduce((s, i) => s + newHeights[i], 0)
      for (const i of donors) {
        const share = total > 0 ? newHeights[i] / total : 1 / donors.length
        newHeights[i] = Math.max(5, newHeights[i] - needed * share)
      }
    }
    newHeights[index] = needed
  }

  panelHeights.value = newHeights
  saveHeights()
}

// flush:'sync' ensures heights update in the same tick as collapse state,
// preventing a two-frame layout jump.
watch(localFilesCollapsed, (val) => handlePanelToggle(0, val), { flush: 'sync' })
watch(localOnlineCollapsed, (val) => handlePanelToggle(1, val), { flush: 'sync' })
watch(localGitCollapsed, (val) => handlePanelToggle(2, val), { flush: 'sync' })
watch(localOutlineCollapsed, (val) => handlePanelToggle(3, val), { flush: 'sync' })

function handleMobileSelect(id) {
  emit('select', id)
  emit('update:mobileOpen', false)
}

// Expose functions for parent components
defineExpose({ refreshGit })
</script>

<style scoped>
/* Tree panel root element - must be styled here (not in parent)
   because LatexTreePanel is a fragment component and parent's
   scoped CSS cannot reach fragment root elements in Vue 3. */
.tree-panel {
  flex-shrink: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  min-width: 0;
  overflow: hidden;
}

.tree-panel.collapsed {
  width: 48px !important;
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.mobile-tree-drawer {
  background-color: rgb(var(--v-theme-surface)) !important;
}

.mobile-tree-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  gap: 4px;
  padding: 8px;
}

/* Collapsed Tree State */
.tree-collapsed {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 4px;
  gap: 12px;
  height: 100%;
}

.collapsed-bar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 0;
  cursor: pointer;
  transition: color 0.2s ease;
}

.collapsed-bar:hover {
  color: var(--llars-primary, #b0ca97);
}

.collapsed-icon-box {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(var(--v-theme-on-surface), 0.05);
  border-radius: 6px;
}

.collapsed-label {
  font-size: 10px;
  font-weight: 500;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  transform: rotate(180deg);
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.expand-icon {
  opacity: 0.5;
}

.collapsed-bar:hover .expand-icon {
  opacity: 1;
}

.collapsed-git-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 6px;
}

.collapsed-git-badge:hover {
  background: rgba(var(--v-theme-warning), 0.15);
  color: rgb(var(--v-theme-warning));
}

.badge-count {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  background: rgb(var(--v-theme-warning));
  color: white;
  border-radius: 10px;
}

/* Sidebar Workspace Header */
.sidebar-workspace-header {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
  min-height: 32px;
}

.sidebar-workspace-name {
  font-size: 12px;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.8);
  flex: 1;
  min-width: 0;
}

/* Online Users Status (connection + ghost text) */
.online-users-status {
  display: flex;
  gap: 4px;
  padding: 4px 8px;
  flex-wrap: wrap;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

/* Tree Expanded */
.tree-expanded {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.tree-stack {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 8px;
  gap: 0;
}


/* Online Users Section (inside TreeStackPanel) */

.online-users-list {
  padding: 2px;
  background: rgb(var(--v-theme-surface));
}

.online-user-item {
  display: flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 4px;
  gap: 8px;
  min-height: 28px;
}

.online-user-item:hover {
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.online-user-avatar-wrap {
  border: 2px solid transparent;
  border-radius: 10px 3px 10px 3px;
  padding: 1px;
  flex-shrink: 0;
  line-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.2s ease;
}

.online-user-avatar-wrap:not(.online):not(.pending) {
  opacity: 0.6;
  border-color: rgba(var(--v-theme-on-surface), 0.12);
}

.online-user-name {
  flex: 1;
  font-size: 0.8rem;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1;
}

.online-user-item:has(.online-user-avatar-wrap:not(.online):not(.pending)) .online-user-name {
  opacity: 0.6;
}

.online-user-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 0 2px rgb(var(--v-theme-surface));
}

/* Pending access requests in COLLABS panel */
.pending-requests-divider {
  padding: 6px 8px 2px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgb(var(--v-theme-warning));
  border-top: 1px dashed rgba(var(--v-theme-warning), 0.3);
  margin-top: 4px;
}

.pending-request-item {
  background: rgba(var(--v-theme-warning), 0.06);
  border-radius: 4px;
}

.online-user-avatar-wrap.pending {
  border: 2px dashed rgba(var(--v-theme-warning), 0.5);
  opacity: 0.7;
}

.pending-request-item .v-btn {
  width: 22px !important;
  height: 22px !important;
  min-width: 22px !important;
}
</style>
