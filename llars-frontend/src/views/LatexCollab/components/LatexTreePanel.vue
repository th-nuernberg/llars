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
      <!-- Files Panel (Mobile) -->
      <TreeStackPanel
        :title="$t('latexCollab.tree.files')"
        icon="mdi-file-tree"
        v-model:collapsed="localFilesCollapsed"
      >
        <template #actions>
          <v-btn icon variant="text" size="x-small" :disabled="!canEdit" @click="$emit('create', { type: 'file' })">
            <LIcon size="16">mdi-file-plus</LIcon>
          </v-btn>
          <v-btn icon variant="text" size="x-small" :disabled="!canEdit" @click="$emit('create', { type: 'folder' })">
            <LIcon size="16">mdi-folder-plus</LIcon>
          </v-btn>
        </template>
        <MarkdownTreePanel
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
      <div class="tree-stack" ref="treeStackRef">
        <!-- Files Panel -->
        <TreeStackPanel
          :title="$t('latexCollab.tree.files')"
          icon="mdi-file-tree"
          v-model:collapsed="localFilesCollapsed"
          :style="getPanelStyle(0)"
        >
          <template #actions>
            <v-btn icon variant="text" size="x-small" :disabled="!canEdit" :title="$t('markdownCollab.tree.actions.newFile')" @click="$emit('create', { type: 'file' })">
              <LIcon size="16">mdi-file-plus</LIcon>
            </v-btn>
            <v-btn icon variant="text" size="x-small" :disabled="!canEdit" :title="$t('markdownCollab.tree.actions.newFolder')" @click="$emit('create', { type: 'folder' })">
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

        <!-- Resize Divider 1 -->
        <PanelResizeDivider
          v-if="!localFilesCollapsed && !localGitCollapsed"
          @resize-start="startPanelResize(0, $event)"
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
          :style="getPanelStyle(1)"
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

        <!-- Resize Divider 2 -->
        <PanelResizeDivider
          v-if="!localGitCollapsed && !localOutlineCollapsed"
          @resize-start="startPanelResize(1, $event)"
          @resize-move="onPanelResize"
          @resize-end="endPanelResize"
        />

        <!-- Outline Panel -->
        <TreeStackPanel
          :title="$t('latexCollab.outline.title')"
          icon="mdi-format-list-bulleted"
          v-model:collapsed="localOutlineCollapsed"
          :style="getPanelStyle(2)"
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

  <!-- Resize Divider: Tree | Content (Desktop only) -->
  <div
    v-if="!isMobile && !treeCollapsed"
    class="resize-divider vertical"
    :class="{ resizing: resizingTree }"
    @mousedown="$emit('start-tree-resize', $event)"
  >
    <div class="resize-handle" />
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
  resizingTree: { type: Boolean, default: false },
  outlineFlatItems: { type: Array, default: () => [] },
  outlineEmptyLabel: { type: String, default: '' },
  isOutlineItemCollapsed: { type: Function, default: () => false },
  // Git props
  canCommit: { type: Boolean, default: false },
  apiPrefix: { type: String, default: '/api/latex-collab' },
  // Collapse states (optional external control)
  filesCollapsed: { type: Boolean, default: false },
  gitCollapsed: { type: Boolean, default: true },
  outlineCollapsed: { type: Boolean, default: false }
})

const emit = defineEmits([
  'update:mobileOpen',
  'update:treeCollapsed',
  'update:filesCollapsed',
  'update:gitCollapsed',
  'update:outlineCollapsed',
  'select',
  'create',
  'rename',
  'remove',
  'move',
  'open-asset-picker',
  'start-tree-resize',
  'navigate-home',
  'navigate-workspaces',
  'toggle-outline-item',
  'jump-to-outline-item',
  'open-git-detail',
  'committed'
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

const localOutlineCollapsed = computed({
  get: () => props.outlineCollapsed,
  set: (val) => emit('update:outlineCollapsed', val)
})

// Git changes badge
const gitTotalChanges = ref(0)

// Git panel refs for external refresh
const gitPanelMobileRef = ref(null)
const gitPanelDesktopRef = ref(null)

/**
 * Refresh the Git panel from external trigger
 */
function refreshGit() {
  gitPanelMobileRef.value?.refresh?.()
  gitPanelDesktopRef.value?.refresh?.()
}

// Panel heights for resize (percentages, 0-100 for each panel)
const treeStackRef = ref(null)
const panelHeights = ref([50, 25, 25]) // Default: 50% files, 25% git, 25% outline
const resizingPanelIndex = ref(-1)
const resizeStartY = ref(0)
const resizeStartHeights = ref([])

// Load saved heights
onMounted(() => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      if (Array.isArray(parsed) && parsed.length === 3) {
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
  const collapsed = [localFilesCollapsed.value, localGitCollapsed.value, localOutlineCollapsed.value]
  if (collapsed[index]) return {}

  // Count expanded panels
  const expandedCount = collapsed.filter(c => !c).length
  if (expandedCount <= 1) return { flex: '1' }

  return {
    flex: `${panelHeights.value[index]} 1 0`,
    minHeight: '80px'
  }
}

function startPanelResize(dividerIndex, event) {
  resizingPanelIndex.value = dividerIndex
  resizeStartY.value = event.y
  resizeStartHeights.value = [...panelHeights.value]
}

function onPanelResize(event) {
  if (resizingPanelIndex.value < 0 || !treeStackRef.value) return

  const containerHeight = treeStackRef.value.clientHeight
  const deltaPercent = (event.deltaY / containerHeight) * 100

  const idx = resizingPanelIndex.value
  const newHeights = [...resizeStartHeights.value]

  // Get the two panels being resized (panel at idx and panel at idx+1)
  const panelAbove = idx === 0 ? 0 : 1 // Which expanded panel is above the divider
  const panelBelow = idx === 0 ? 1 : 2 // Which expanded panel is below the divider

  // Adjust heights
  newHeights[panelAbove] = Math.max(10, resizeStartHeights.value[panelAbove] + deltaPercent)
  newHeights[panelBelow] = Math.max(10, resizeStartHeights.value[panelBelow] - deltaPercent)

  panelHeights.value = newHeights
}

function endPanelResize() {
  resizingPanelIndex.value = -1
  saveHeights()
}

function handleMobileSelect(id) {
  emit('select', id)
  emit('update:mobileOpen', false)
}

// Expose functions for parent components
defineExpose({ refreshGit })
</script>

<style scoped>
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
</style>
