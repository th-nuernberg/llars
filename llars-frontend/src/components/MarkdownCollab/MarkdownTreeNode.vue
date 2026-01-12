<template>
  <div :class="{ 'node-new': isRecentlyAdded, 'node-zotero': node.is_zotero_managed }">
    <div
      class="tree-row"
      :class="{ selected: selectedId === node.id, 'zotero-managed': node.is_zotero_managed }"
      :style="{ paddingLeft: `${12 + level * 14}px` }"
      @click="$emit('select', node.id)"
    >
      <button
        v-if="node.type === 'folder'"
        class="expand-btn"
        type="button"
        @click.stop="$emit('toggle', node.id)"
        :title="isExpanded ? $t('markdownCollab.tree.actions.collapse') : $t('markdownCollab.tree.actions.expand')"
      >
        <LIcon size="18" class="text-medium-emphasis">
          {{ isExpanded ? 'mdi-chevron-down' : 'mdi-chevron-right' }}
        </LIcon>
      </button>
      <span v-else class="expand-spacer" />

      <LIcon size="20" class="mr-2" :color="nodeIconColor">
        {{ nodeIcon }}
      </LIcon>

      <span class="tree-title text-truncate">{{ node.title }}</span>

      <!-- Zotero badge for managed files -->
      <v-chip
        v-if="node.is_zotero_managed"
        size="x-small"
        variant="tonal"
        color="teal"
        class="ml-1 zotero-badge"
        :title="$t('markdownCollab.tree.zoteroReadonly')"
      >
        <LIcon size="12" start>mdi-book-open-variant</LIcon>
        Zotero
      </v-chip>

      <v-spacer />

      <!-- Hide edit actions for Zotero-managed files -->
      <div v-if="canEdit && !node.is_zotero_managed" class="tree-actions" @click.stop>
        <v-btn
          v-if="node.type === 'folder'"
          size="x-small"
          variant="text"
          icon="mdi-file-document-plus-outline"
          :title="$t('markdownCollab.tree.actions.newFile')"
          @click="$emit('create', { parentId: node.id, type: 'file' })"
        />
        <v-btn
          v-if="node.type === 'folder'"
          size="x-small"
          variant="text"
          icon="mdi-folder-plus-outline"
          :title="$t('markdownCollab.tree.actions.newFolder')"
          @click="$emit('create', { parentId: node.id, type: 'folder' })"
        />
        <v-btn
          size="x-small"
          variant="text"
          icon="mdi-rename-box"
          :title="$t('markdownCollab.tree.actions.rename')"
          @click="$emit('rename', node)"
        />
        <v-btn
          size="x-small"
          variant="text"
          icon="mdi-delete-outline"
          :title="$t('markdownCollab.tree.actions.delete')"
          @click="$emit('remove', node)"
        />
      </div>
    </div>

    <div v-if="node.type === 'folder' && isExpanded" class="children">
      <draggable
        v-if="dragEnabled"
        :list="node.children"
        item-key="id"
        :group="{ name: 'markdown-tree', pull: true, put: true }"
        handle=".drag-handle"
        :animation="150"
        @change="(evt) => emitMove(evt, node.id)"
      >
          <template #item="{ element }">
          <div class="drag-wrapper">
            <span class="drag-handle" :title="$t('markdownCollab.tree.actions.drag')">
              <LIcon size="14" class="text-medium-emphasis">mdi-drag</LIcon>
            </span>
            <MarkdownTreeNode
              :node="element"
              :selected-id="selectedId"
              :expanded-ids="expandedIds"
              :level="level + 1"
              :can-edit="canEdit"
              :drag-enabled="dragEnabled"
              :recently-added-ids="recentlyAddedIds"
              :file-icon="fileIcon"
              :file-icon-color="fileIconColor"
              :folder-icon="folderIcon"
              :folder-open-icon="folderOpenIcon"
              @select="$emit('select', $event)"
              @toggle="$emit('toggle', $event)"
              @create="$emit('create', $event)"
              @rename="$emit('rename', $event)"
              @remove="$emit('remove', $event)"
              @move="$emit('move', $event)"
            />
          </div>
        </template>
      </draggable>

      <template v-else>
        <MarkdownTreeNode
          v-for="child in node.children"
          :key="child.id"
          :node="child"
          :selected-id="selectedId"
          :expanded-ids="expandedIds"
          :level="level + 1"
          :can-edit="canEdit"
          :drag-enabled="dragEnabled"
          :recently-added-ids="recentlyAddedIds"
          :file-icon="fileIcon"
          :file-icon-color="fileIconColor"
          :folder-icon="folderIcon"
          :folder-open-icon="folderOpenIcon"
          @select="$emit('select', $event)"
          @toggle="$emit('toggle', $event)"
          @create="$emit('create', $event)"
          @rename="$emit('rename', $event)"
          @remove="$emit('remove', $event)"
          @move="$emit('move', $event)"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import draggable from 'vuedraggable'

defineOptions({ name: 'MarkdownTreeNode' })

const props = defineProps({
  node: { type: Object, required: true },
  selectedId: { type: Number, default: null },
  expandedIds: { type: Object, required: true }, // Set<number>
  level: { type: Number, default: 0 },
  canEdit: { type: Boolean, default: false },
  dragEnabled: { type: Boolean, default: false },
  recentlyAddedIds: { type: Set, default: () => new Set() },
  fileIcon: { type: String, default: 'mdi-language-markdown' },
  fileIconColor: { type: String, default: 'info' },
  folderIcon: { type: String, default: 'mdi-folder' },
  folderOpenIcon: { type: String, default: 'mdi-folder-open' }
})

const emit = defineEmits(['select', 'toggle', 'create', 'rename', 'remove', 'move'])

const isExpanded = computed(() => props.expandedIds.has(props.node.id))
const isRecentlyAdded = computed(() => props.recentlyAddedIds.has(props.node.id))

// Compute icon based on node type and Zotero status
const nodeIcon = computed(() => {
  if (props.node.type === 'folder') {
    return isExpanded.value ? props.folderOpenIcon : props.folderIcon
  }
  // Zotero-managed .bib files get a special icon
  if (props.node.is_zotero_managed) {
    return 'mdi-bookshelf'
  }
  return props.fileIcon
})

const nodeIconColor = computed(() => {
  if (props.node.type === 'folder') {
    return 'primary'
  }
  // Zotero-managed files get teal color
  if (props.node.is_zotero_managed) {
    return 'teal'
  }
  return props.fileIconColor
})

function emitMove(evt, parentId) {
  const moved = evt?.moved
  const added = evt?.added
  const element = moved?.element || added?.element
  const newIndex = moved?.newIndex ?? added?.newIndex
  if (!element || typeof newIndex !== 'number') return
  // Root uses parentId=null; children use folder id
  const normalizedParentId = parentId ?? null
  emit('move', { id: element.id, parentId: normalizedParentId, orderIndex: newIndex })
}
</script>

<style scoped>
.tree-row {
  display: flex;
  align-items: center;
  gap: 2px;
  height: 34px;
  border-radius: 8px;
  cursor: pointer;
  color: rgb(var(--v-theme-on-surface));
  transition: background-color 0.12s ease;
}

.tree-row:hover {
  background: rgba(var(--v-theme-primary), 0.08);
}

.tree-row.selected {
  background: rgba(var(--v-theme-primary), 0.14);
}

.expand-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.expand-btn:hover {
  background: rgba(var(--v-theme-on-surface), 0.06);
}

.expand-spacer {
  width: 28px;
  height: 28px;
}

.tree-title {
  font-size: 0.9rem;
  line-height: 1;
}

.tree-actions {
  display: none;
}

.tree-row:hover .tree-actions {
  display: inline-flex;
  gap: 2px;
}

.children {
  margin-top: 2px;
}

.drag-wrapper {
  display: flex;
  align-items: stretch;
}

.drag-handle {
  width: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  user-select: none;
  opacity: 0.5;
}

.drag-wrapper:hover .drag-handle {
  opacity: 0.9;
}

/* Animation for new nodes */
.node-new {
  animation: nodeAppear 0.5s ease-out;
}

.node-new .tree-row {
  background: rgba(var(--v-theme-success), 0.15);
  animation: nodeHighlight 2s ease-out forwards;
}

@keyframes nodeAppear {
  0% {
    opacity: 0;
    transform: translateX(-20px);
  }
  100% {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes nodeHighlight {
  0% {
    background: rgba(var(--v-theme-success), 0.25);
    box-shadow: 0 0 8px rgba(var(--v-theme-success), 0.4);
  }
  70% {
    background: rgba(var(--v-theme-success), 0.12);
    box-shadow: 0 0 4px rgba(var(--v-theme-success), 0.2);
  }
  100% {
    background: transparent;
    box-shadow: none;
  }
}

/* Zotero-managed file styles */
.node-zotero .tree-row {
  border-left: 3px solid #009688;
}

.tree-row.zotero-managed {
  background: rgba(0, 150, 136, 0.06);
}

.tree-row.zotero-managed:hover {
  background: rgba(0, 150, 136, 0.12);
}

.tree-row.zotero-managed.selected {
  background: rgba(0, 150, 136, 0.18);
}

.zotero-badge {
  height: 18px !important;
  font-size: 10px !important;
  padding: 0 6px !important;
}

.zotero-badge .v-icon {
  margin-right: 2px !important;
}
</style>
