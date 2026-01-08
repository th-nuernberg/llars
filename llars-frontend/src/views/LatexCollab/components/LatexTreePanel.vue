<!--
  LatexTreePanel.vue

  Combined tree panel for LaTeX workspace.
  Handles both mobile drawer and desktop sidebar with document tree and outline.
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
      <div class="tree-main">
        <MarkdownTreePanel
          :workspace-id="workspaceId"
          :nodes="nodes"
          :selected-id="selectedId"
          :loading="loading"
          :can-edit="canEdit"
          :recently-added-ids="recentlyAddedIds"
          file-placeholder="z. B. main.tex"
          file-icon="mdi-file-code-outline"
          file-icon-color="primary"
          @select="handleMobileSelect"
          @create="$emit('create', $event)"
          @rename="$emit('rename', $event)"
          @remove="$emit('remove', $event)"
          @move="$emit('move', $event)"
        />
      </div>
      <OutlinePanel
        :collapsed="outlineCollapsed"
        :items="outlineFlatItems"
        :empty-label="outlineEmptyLabel"
        :is-item-collapsed="isOutlineItemCollapsed"
        @toggle-collapsed="$emit('toggle-outline-collapsed')"
        @toggle-item="$emit('toggle-outline-item', $event)"
        @jump-to-item="$emit('jump-to-outline-item', $event)"
      />
    </div>
    <template #append>
      <v-divider />
      <v-list density="compact" class="pa-2">
        <v-list-item
          prepend-icon="mdi-home"
          title="Startseite"
          @click="$emit('navigate-home')"
        />
        <v-list-item
          prepend-icon="mdi-folder-multiple"
          title="Alle Workspaces"
          @click="$emit('navigate-workspaces')"
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
    <div v-if="treeCollapsed" class="tree-collapsed" @click="$emit('update:treeCollapsed', false)">
      <div class="collapsed-bar">
        <div class="collapsed-icon-box">
          <LIcon size="18">mdi-file-tree</LIcon>
        </div>
        <span class="collapsed-label">Dateien</span>
        <v-spacer />
        <LIcon size="18" class="expand-icon">mdi-chevron-right</LIcon>
      </div>
    </div>

    <!-- Expanded State -->
    <div v-else class="tree-expanded">
      <div class="tree-stack">
        <div class="tree-main">
          <MarkdownTreePanel
            :workspace-id="workspaceId"
            :nodes="nodes"
            :selected-id="selectedId"
            :loading="loading"
            :can-edit="canEdit"
            :recently-added-ids="recentlyAddedIds"
            file-placeholder="z. B. main.tex"
            file-icon="mdi-file-code-outline"
            file-icon-color="primary"
            @select="$emit('select', $event)"
            @create="$emit('create', $event)"
            @rename="$emit('rename', $event)"
            @remove="$emit('remove', $event)"
            @move="$emit('move', $event)"
          >
            <template #header-append>
              <v-btn
                icon
                variant="text"
                size="small"
                title="Asset hochladen"
                @click.stop="$emit('open-asset-picker')"
              >
                <LIcon size="18">mdi-paperclip</LIcon>
              </v-btn>
              <v-btn
                icon
                variant="text"
                size="small"
                title="Einklappen"
                @click.stop="$emit('update:treeCollapsed', true)"
              >
                <LIcon size="18">mdi-chevron-left</LIcon>
              </v-btn>
            </template>
          </MarkdownTreePanel>
        </div>
        <OutlinePanel
          :collapsed="outlineCollapsed"
          :items="outlineFlatItems"
          :empty-label="outlineEmptyLabel"
          :is-item-collapsed="isOutlineItemCollapsed"
          @toggle-collapsed="$emit('toggle-outline-collapsed')"
          @toggle-item="$emit('toggle-outline-item', $event)"
          @jump-to-item="$emit('jump-to-outline-item', $event)"
        />
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
import MarkdownTreePanel from '@/components/MarkdownCollab/MarkdownTreePanel.vue'
import OutlinePanel from './OutlinePanel.vue'

defineProps({
  isMobile: {
    type: Boolean,
    default: false
  },
  mobileOpen: {
    type: Boolean,
    default: false
  },
  workspaceId: {
    type: Number,
    required: true
  },
  nodes: {
    type: Array,
    default: () => []
  },
  selectedId: {
    type: Number,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  canEdit: {
    type: Boolean,
    default: false
  },
  recentlyAddedIds: {
    type: Set,
    default: () => new Set()
  },
  treeCollapsed: {
    type: Boolean,
    default: false
  },
  treePanelWidth: {
    type: Number,
    default: 280
  },
  resizingTree: {
    type: Boolean,
    default: false
  },
  outlineCollapsed: {
    type: Boolean,
    default: false
  },
  outlineFlatItems: {
    type: Array,
    default: () => []
  },
  outlineEmptyLabel: {
    type: String,
    default: 'Kein Dokument'
  },
  isOutlineItemCollapsed: {
    type: Function,
    default: () => false
  }
})

const emit = defineEmits([
  'update:mobileOpen',
  'update:treeCollapsed',
  'select',
  'create',
  'rename',
  'remove',
  'move',
  'open-asset-picker',
  'start-tree-resize',
  'navigate-home',
  'navigate-workspaces',
  'toggle-outline-collapsed',
  'toggle-outline-item',
  'jump-to-outline-item'
])

function handleMobileSelect(id) {
  emit('select', id)
  emit('update:mobileOpen', false)
}
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
}

.tree-main {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
</style>
