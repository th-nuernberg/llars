<template>
  <div>
    <div
      class="tree-row"
      :class="{ selected: selectedId === node.id }"
      :style="{ paddingLeft: `${12 + level * 14}px` }"
      @click="$emit('select', node.id)"
    >
      <button
        v-if="node.type === 'folder'"
        class="expand-btn"
        type="button"
        @click.stop="$emit('toggle', node.id)"
        :title="isExpanded ? 'Einklappen' : 'Ausklappen'"
      >
        <v-icon size="18" class="text-medium-emphasis">
          {{ isExpanded ? 'mdi-chevron-down' : 'mdi-chevron-right' }}
        </v-icon>
      </button>
      <span v-else class="expand-spacer" />

      <v-icon size="20" class="mr-2" :color="node.type === 'folder' ? 'primary' : 'info'">
        {{ node.type === 'folder' ? (isExpanded ? 'mdi-folder-open' : 'mdi-folder') : 'mdi-language-markdown' }}
      </v-icon>

      <span class="tree-title text-truncate">{{ node.title }}</span>

      <v-spacer />

      <div v-if="canEdit" class="tree-actions" @click.stop>
        <v-btn
          v-if="node.type === 'folder'"
          size="x-small"
          variant="text"
          icon="mdi-file-document-plus-outline"
          title="Neue Datei"
          @click="$emit('create', { parentId: node.id, type: 'file' })"
        />
        <v-btn
          v-if="node.type === 'folder'"
          size="x-small"
          variant="text"
          icon="mdi-folder-plus-outline"
          title="Neuer Ordner"
          @click="$emit('create', { parentId: node.id, type: 'folder' })"
        />
        <v-btn
          size="x-small"
          variant="text"
          icon="mdi-rename-box"
          title="Umbenennen"
          @click="$emit('rename', node)"
        />
        <v-btn
          size="x-small"
          variant="text"
          icon="mdi-delete-outline"
          title="Löschen"
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
            <span class="drag-handle" title="Ziehen">
              <v-icon size="14" class="text-medium-emphasis">mdi-drag</v-icon>
            </span>
            <MarkdownTreeNode
              :node="element"
              :selected-id="selectedId"
              :expanded-ids="expandedIds"
              :level="level + 1"
              :can-edit="canEdit"
              :drag-enabled="dragEnabled"
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
  dragEnabled: { type: Boolean, default: false }
})

const emit = defineEmits(['select', 'toggle', 'create', 'rename', 'remove', 'move'])

const isExpanded = computed(() => props.expandedIds.has(props.node.id))

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
</style>
