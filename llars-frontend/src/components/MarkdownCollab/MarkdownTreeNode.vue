<template>
  <div
    class="tree-node"
    :class="{
      'node-new': isRecentlyAdded,
      'node-zotero': node.is_zotero_managed
    }"
  >
    <!-- Main Row with integrated drop detection -->
    <div
      ref="rowRef"
      class="tree-row"
      :class="{
        selected: selectedId === node.id,
        'zotero-managed': node.is_zotero_managed,
        folder: node.type === 'folder',
        dragging: isDragging,
        'drop-above': dropPosition === 'above',
        'drop-below': dropPosition === 'below',
        'drop-inside': dropPosition === 'inside'
      }"
      :draggable="dragEnabled && !node.is_zotero_managed"
      :style="{ paddingLeft: `${8 + level * 16}px` }"
      @click="handleRowClick"
      @dragstart="onDragStart"
      @dragend="onDragEnd"
      @dragover.prevent="onRowDragOver"
      @dragleave="onRowDragLeave"
      @drop="onRowDrop"
    >
      <!-- Indent Guide Lines -->
      <div class="indent-guides">
        <span
          v-for="i in level"
          :key="i"
          class="indent-line"
          :style="{ left: `${8 + (i - 1) * 16 + 8}px` }"
        />
      </div>

      <!-- Expand/Collapse for folders -->
      <button
        v-if="node.type === 'folder'"
        class="expand-btn"
        type="button"
        @click.stop="$emit('toggle', node.id)"
        :title="isExpanded ? $t('markdownCollab.tree.actions.collapse') : $t('markdownCollab.tree.actions.expand')"
      >
        <LIcon size="16" class="expand-icon" :class="{ expanded: isExpanded }">
          mdi-chevron-right
        </LIcon>
      </button>
      <span v-else class="expand-spacer" />

      <!-- Icon -->
      <LIcon size="18" class="node-icon" :color="nodeIconColor">
        {{ nodeIcon }}
      </LIcon>

      <!-- Title -->
      <span class="tree-title">{{ node.title }}</span>

      <!-- Zotero badge -->
      <span v-if="node.is_zotero_managed" class="zotero-badge">
        <LIcon size="10">zotero</LIcon>
      </span>

      <!-- Main document indicator -->
      <LIcon v-if="node.is_main" size="14" color="warning" class="main-badge" title="Hauptdokument">
        mdi-star
      </LIcon>

      <span class="flex-spacer" />

      <!-- Actions -->
      <div v-if="canEdit && !node.is_zotero_managed" class="tree-actions">
        <button
          v-if="node.type === 'folder'"
          class="action-btn"
          type="button"
          :title="$t('markdownCollab.tree.actions.newFile')"
          @click.stop="$emit('create', { parentId: node.id, type: 'file' })"
        >
          <LIcon size="14">mdi-file-plus</LIcon>
        </button>
        <button
          class="action-btn"
          type="button"
          :title="$t('markdownCollab.tree.actions.rename')"
          @click.stop="$emit('rename', node)"
        >
          <LIcon size="14">mdi-pencil</LIcon>
        </button>
        <button
          class="action-btn delete"
          type="button"
          :title="$t('markdownCollab.tree.actions.delete')"
          @click.stop="$emit('remove', node)"
        >
          <LIcon size="14">mdi-trash-can-outline</LIcon>
        </button>
      </div>
    </div>

    <!-- Children (for folders) -->
    <div v-if="node.type === 'folder' && isExpanded" class="children">
      <MarkdownTreeNode
        v-for="(child, index) in node.children"
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
        :sibling-index="index"
        :sibling-count="node.children.length"
        @select="$emit('select', $event)"
        @toggle="$emit('toggle', $event)"
        @create="$emit('create', $event)"
        @rename="$emit('rename', $event)"
        @remove="$emit('remove', $event)"
        @move="$emit('move', $event)"
      />

      <!-- Drop zone at END of folder children (empty folder or after last child) -->
      <div
        v-if="dragEnabled"
        class="folder-end-zone"
        :class="{ active: dropPosition === 'end' }"
        @dragover.prevent="onEndZoneDragOver"
        @dragleave="onEndZoneDragLeave"
        @drop="onEndZoneDrop"
      >
        <span class="end-zone-line" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

defineOptions({ name: 'MarkdownTreeNode' })

const props = defineProps({
  node: { type: Object, required: true },
  selectedId: { type: Number, default: null },
  expandedIds: { type: Object, required: true },
  level: { type: Number, default: 0 },
  canEdit: { type: Boolean, default: false },
  dragEnabled: { type: Boolean, default: false },
  recentlyAddedIds: { type: Set, default: () => new Set() },
  fileIcon: { type: String, default: 'mdi-language-markdown' },
  fileIconColor: { type: String, default: 'info' },
  folderIcon: { type: String, default: 'mdi-folder' },
  folderOpenIcon: { type: String, default: 'mdi-folder-open' },
  siblingIndex: { type: Number, default: 0 },
  siblingCount: { type: Number, default: 1 }
})

const emit = defineEmits(['select', 'toggle', 'create', 'rename', 'remove', 'move'])

const rowRef = ref(null)
const isDragging = ref(false)
const dropPosition = ref(null) // 'above', 'below', 'inside', 'end'

const isExpanded = computed(() => props.expandedIds.has(props.node.id))
const isRecentlyAdded = computed(() => props.recentlyAddedIds.has(props.node.id))

const nodeIcon = computed(() => {
  if (props.node.type === 'folder') {
    return isExpanded.value ? props.folderOpenIcon : props.folderIcon
  }
  if (props.node.is_zotero_managed) {
    return 'mdi-bookshelf'
  }
  return props.fileIcon
})

const nodeIconColor = computed(() => {
  if (props.node.type === 'folder') {
    return 'primary'
  }
  if (props.node.is_zotero_managed) {
    return 'teal'
  }
  return props.fileIconColor
})

function handleRowClick() {
  if (props.node.type === 'folder') {
    emit('toggle', props.node.id)
  }
  emit('select', props.node.id)
}

// Drag handlers
function onDragStart(e) {
  if (!props.dragEnabled || props.node.is_zotero_managed) {
    e.preventDefault()
    return
  }
  isDragging.value = true
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', JSON.stringify({
    id: props.node.id,
    type: props.node.type,
    parentId: props.node.parent_id
  }))
}

function onDragEnd() {
  isDragging.value = false
  dropPosition.value = null
}

// Calculate drop position based on mouse Y within the row
function calculateDropPosition(e) {
  if (!rowRef.value) return null

  const rect = rowRef.value.getBoundingClientRect()
  const y = e.clientY - rect.top
  const height = rect.height

  // For folders: top 25% = above, middle 50% = inside, bottom 25% = below
  // For files: top 50% = above, bottom 50% = below
  if (props.node.type === 'folder') {
    if (y < height * 0.25) return 'above'
    if (y > height * 0.75) return 'below'
    return 'inside'
  } else {
    return y < height * 0.5 ? 'above' : 'below'
  }
}

function onRowDragOver(e) {
  if (!props.dragEnabled || props.node.is_zotero_managed) return

  e.preventDefault()
  e.stopPropagation()

  // Check if dragging self
  try {
    if (!e.dataTransfer.types.includes('text/plain')) return
  } catch { return }

  const pos = calculateDropPosition(e)
  dropPosition.value = pos
  e.dataTransfer.dropEffect = 'move'
}

function onRowDragLeave(e) {
  // Only clear if actually leaving the row
  const currentTarget = e.currentTarget
  if (currentTarget && e.relatedTarget && currentTarget.contains(e.relatedTarget)) {
    return
  }
  dropPosition.value = null
}

function onRowDrop(e) {
  e.preventDefault()
  e.stopPropagation()

  if (!props.dragEnabled) return

  try {
    const data = JSON.parse(e.dataTransfer.getData('text/plain'))

    // Don't drop on self
    if (data.id === props.node.id) {
      dropPosition.value = null
      return
    }

    const pos = dropPosition.value || calculateDropPosition(e)
    let targetParentId
    let orderIndex

    if (pos === 'above') {
      // Drop above this node - same parent as this node
      targetParentId = props.node.parent_id ?? null
      orderIndex = props.siblingIndex
    } else if (pos === 'below') {
      // Drop below this node - same parent as this node
      targetParentId = props.node.parent_id ?? null
      orderIndex = props.siblingIndex + 1
    } else if (pos === 'inside') {
      // Drop inside this folder - at the beginning
      targetParentId = props.node.id
      orderIndex = 0
      // Auto-expand the folder
      if (!isExpanded.value) {
        emit('toggle', props.node.id)
      }
    }

    emit('move', {
      id: data.id,
      parentId: targetParentId,
      orderIndex
    })
  } catch (err) {
    console.error('Drop error:', err)
  }

  dropPosition.value = null
}

// End zone handlers (for dropping at end of folder children)
function onEndZoneDragOver(e) {
  e.preventDefault()
  e.stopPropagation()
  dropPosition.value = 'end'
  e.dataTransfer.dropEffect = 'move'
}

function onEndZoneDragLeave(e) {
  if (e.currentTarget && e.relatedTarget && e.currentTarget.contains(e.relatedTarget)) {
    return
  }
  dropPosition.value = null
}

function onEndZoneDrop(e) {
  e.preventDefault()
  e.stopPropagation()

  if (!props.dragEnabled) return

  try {
    const data = JSON.parse(e.dataTransfer.getData('text/plain'))

    // Don't drop folder into itself
    if (data.id === props.node.id) {
      dropPosition.value = null
      return
    }

    emit('move', {
      id: data.id,
      parentId: props.node.id,
      orderIndex: props.node.children?.length || 0
    })
  } catch (err) {
    console.error('End zone drop error:', err)
  }

  dropPosition.value = null
}
</script>

<style scoped>
.tree-node {
  position: relative;
}

/* Main Row */
.tree-row {
  position: relative;
  display: flex;
  align-items: center;
  height: 28px;
  padding-right: 8px;
  margin: 1px 4px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.1s ease;
}

.tree-row:hover {
  background: rgba(var(--v-theme-on-surface), 0.06);
}

.tree-row.selected {
  background: rgba(var(--v-theme-primary), 0.15);
}

.tree-row.selected:hover {
  background: rgba(var(--v-theme-primary), 0.2);
}

.tree-row.folder {
  font-weight: 500;
}

.tree-row.dragging {
  opacity: 0.4;
  background: rgba(var(--v-theme-primary), 0.1);
}

/* Drop position indicators - lines above/below */
.tree-row::before,
.tree-row::after {
  content: '';
  position: absolute;
  left: 4px;
  right: 4px;
  height: 3px;
  background: var(--llars-primary, #b0ca97);
  border-radius: 2px;
  opacity: 0;
  transition: opacity 0.1s ease;
  pointer-events: none;
  box-shadow: 0 0 6px rgba(176, 202, 151, 0.6);
}

.tree-row::before {
  top: -2px;
}

.tree-row::after {
  bottom: -2px;
}

.tree-row.drop-above::before {
  opacity: 1;
}

.tree-row.drop-below::after {
  opacity: 1;
}

.tree-row.drop-inside {
  background: rgba(var(--v-theme-primary), 0.25);
  outline: 2px solid var(--llars-primary, #b0ca97);
  outline-offset: -2px;
}

/* Indent Guide Lines */
.indent-guides {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  pointer-events: none;
}

.indent-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 1px;
  background: rgba(var(--v-theme-on-surface), 0.1);
}

.tree-row:hover .indent-line {
  background: rgba(var(--v-theme-on-surface), 0.2);
}

/* Expand Button */
.expand-btn {
  width: 20px;
  height: 20px;
  padding: 0;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: rgba(var(--v-theme-on-surface), 0.5);
  z-index: 1;
}

.expand-btn:hover {
  background: rgba(var(--v-theme-on-surface), 0.1);
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.expand-icon {
  transition: transform 0.15s ease;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.expand-spacer {
  width: 20px;
  flex-shrink: 0;
}

/* Node Icon */
.node-icon {
  flex-shrink: 0;
  margin-right: 6px;
}

/* Title */
.tree-title {
  font-size: 13px;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: rgba(var(--v-theme-on-surface), 0.9);
}

.flex-spacer {
  flex: 1;
  min-width: 8px;
}

/* Badges */
.zotero-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  margin-left: 4px;
  border-radius: 3px;
  background: rgba(0, 150, 136, 0.15);
  color: #009688;
}

.main-badge {
  margin-left: 4px;
}

/* Actions */
.tree-actions {
  display: none;
  align-items: center;
  gap: 2px;
  margin-left: 4px;
}

.tree-row:hover .tree-actions {
  display: flex;
}

.action-btn {
  width: 22px;
  height: 22px;
  padding: 0;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(var(--v-theme-on-surface), 0.5);
  transition: all 0.1s ease;
}

.action-btn:hover {
  background: rgba(var(--v-theme-on-surface), 0.1);
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.action-btn.delete:hover {
  background: rgba(var(--v-theme-error), 0.1);
  color: rgb(var(--v-theme-error));
}

/* Children */
.children {
  position: relative;
}

/* Folder end zone - drop area at end of folder */
.folder-end-zone {
  height: 16px;
  margin: 0 8px;
  position: relative;
  cursor: default;
}

.folder-end-zone .end-zone-line {
  position: absolute;
  left: 24px;
  right: 0;
  top: 50%;
  height: 3px;
  transform: translateY(-50%);
  background: transparent;
  border-radius: 2px;
  transition: all 0.1s ease;
}

.folder-end-zone.active .end-zone-line {
  background: var(--llars-primary, #b0ca97);
  box-shadow: 0 0 6px rgba(176, 202, 151, 0.6);
}

/* Animation for new nodes */
.node-new > .tree-row {
  animation: nodeHighlight 1.5s ease-out forwards;
}

@keyframes nodeHighlight {
  0% {
    background: rgba(var(--v-theme-success), 0.3);
  }
  100% {
    background: transparent;
  }
}

/* Zotero-managed styles */
.node-zotero > .tree-row {
  border-left: 2px solid #009688;
}

.tree-row.zotero-managed {
  background: rgba(0, 150, 136, 0.04);
}

.tree-row.zotero-managed:hover {
  background: rgba(0, 150, 136, 0.08);
}

/* Dragging cursor */
.tree-row[draggable="true"] {
  cursor: grab;
}

.tree-row[draggable="true"]:active {
  cursor: grabbing;
}
</style>
