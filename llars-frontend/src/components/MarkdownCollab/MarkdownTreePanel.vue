<template>
  <div class="tree-panel">
    <div class="tree-header">
      <LIcon size="20" class="header-icon">mdi-file-tree</LIcon>
      <span class="header-title">Workspace</span>
      <div class="header-actions">
        <v-btn
          icon
          variant="text"
          size="x-small"
          :disabled="!canEdit"
          title="Neue Datei"
          @click="openCreateDialog('file')"
        >
          <LIcon size="18">mdi-file-document-plus-outline</LIcon>
        </v-btn>
        <v-btn
          icon
          variant="text"
          size="x-small"
          :disabled="!canEdit"
          title="Neuer Ordner"
          @click="openCreateDialog('folder')"
        >
          <LIcon size="18">mdi-folder-plus-outline</LIcon>
        </v-btn>
        <slot name="header-append" />
      </div>
    </div>

    <div class="search-container">
      <v-text-field
        v-model="filterText"
        density="compact"
        variant="outlined"
        hide-details
        placeholder="Suchen…"
        prepend-inner-icon="mdi-magnify"
        class="tree-search"
      />
    </div>

    <div class="tree-body">
      <v-skeleton-loader v-if="loading" type="list-item@10" class="px-3 pt-2" />

      <div v-else class="tree-scroll px-2 pb-2">
        <draggable
          v-if="dragEnabled"
          :list="localNodes"
          item-key="id"
          :group="{ name: 'markdown-tree', pull: true, put: true }"
          handle=".drag-handle"
          :animation="150"
          @change="(evt) => emitMove(evt, null)"
        >
          <template #item="{ element }">
            <div class="drag-wrapper">
              <span class="drag-handle" title="Ziehen">
                <LIcon size="14" class="text-medium-emphasis">mdi-drag</LIcon>
              </span>
              <MarkdownTreeNode
                :node="element"
                :selected-id="selectedId"
                :expanded-ids="expandedIds"
                :can-edit="canEdit"
                :drag-enabled="dragEnabled"
                :recently-added-ids="recentlyAddedIds"
                :file-icon="fileIcon"
                :file-icon-color="fileIconColor"
                :folder-icon="folderIcon"
                :folder-open-icon="folderOpenIcon"
                @select="$emit('select', $event)"
                @toggle="toggleExpand"
                @create="(p) => openCreateDialog(p.type, p.parentId)"
                @rename="openRenameDialog"
                @remove="openDeleteDialog"
                @move="$emit('move', $event)"
              />
            </div>
          </template>
        </draggable>

        <template v-else>
          <MarkdownTreeNode
            v-for="node in filteredNodes"
            :key="node.id"
            :node="node"
            :selected-id="selectedId"
            :expanded-ids="expandedIds"
            :can-edit="canEdit"
            :drag-enabled="false"
            :recently-added-ids="recentlyAddedIds"
            :file-icon="fileIcon"
            :file-icon-color="fileIconColor"
            :folder-icon="folderIcon"
            :folder-open-icon="folderOpenIcon"
            @select="$emit('select', $event)"
            @toggle="toggleExpand"
            @create="(p) => openCreateDialog(p.type, p.parentId)"
            @rename="openRenameDialog"
            @remove="openDeleteDialog"
            @move="$emit('move', $event)"
          />
        </template>
      </div>
    </div>

    <!-- Create -->
    <v-dialog v-model="createDialog" max-width="520">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon class="mr-2">{{ createType === 'folder' ? 'mdi-folder-plus-outline' : 'mdi-file-document-plus-outline' }}</LIcon>
          {{ createType === 'folder' ? 'Neuer Ordner' : 'Neue Datei' }}
          <v-spacer />
          <LIconBtn icon="mdi-close" tooltip="Schließen" @click="createDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-alert v-if="createError" type="error" variant="tonal" class="mb-4">
            {{ createError }}
          </v-alert>
          <v-text-field
            v-model="createTitle"
            label="Name"
            :placeholder="createType === 'folder' ? 'z. B. Research' : filePlaceholder"
            variant="outlined"
            density="comfortable"
            autofocus
          />
          <div class="text-caption text-medium-emphasis">
            Ziel: {{ createParentLabel }}
          </div>
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" title="Erstellen abbrechen" @click="createDialog = false">Abbrechen</v-btn>
          <v-btn color="primary" title="Datei/Ordner erstellen" :disabled="!canSubmitCreate" @click="submitCreate">
            Erstellen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Rename -->
    <v-dialog v-model="renameDialog" max-width="520">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon class="mr-2">mdi-rename-box</LIcon>
          Umbenennen
          <v-spacer />
          <LIconBtn icon="mdi-close" tooltip="Schließen" @click="renameDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-alert v-if="renameError" type="error" variant="tonal" class="mb-4">
            {{ renameError }}
          </v-alert>
          <v-text-field
            v-model="renameTitle"
            label="Name"
            variant="outlined"
            density="comfortable"
            autofocus
          />
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" title="Umbenennen abbrechen" @click="renameDialog = false">Abbrechen</v-btn>
          <v-btn color="primary" title="Namen speichern" :disabled="!canSubmitRename" @click="submitRename">Speichern</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete -->
    <v-dialog v-model="deleteDialog" max-width="520">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon class="mr-2" color="error">mdi-delete-outline</LIcon>
          Löschen
          <v-spacer />
          <LIconBtn icon="mdi-close" tooltip="Schließen" @click="deleteDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text>
          <div class="text-body-1">
            Möchtest du <strong>{{ pendingDelete?.title }}</strong> wirklich löschen?
          </div>
          <div class="text-caption text-medium-emphasis mt-2">
            Ordner werden rekursiv gelöscht.
          </div>
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" title="Löschen abbrechen" @click="deleteDialog = false">Abbrechen</v-btn>
          <v-btn color="error" title="Ausgewählten Eintrag löschen" @click="submitDelete">Löschen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import draggable from 'vuedraggable'
import MarkdownTreeNode from './MarkdownTreeNode.vue'

const props = defineProps({
  workspaceId: { type: Number, required: true },
  nodes: { type: Array, default: () => [] },
  selectedId: { type: Number, default: null },
  loading: { type: Boolean, default: false },
  canEdit: { type: Boolean, default: false },
  recentlyAddedIds: { type: Set, default: () => new Set() },
  filePlaceholder: { type: String, default: 'z. B. intro.md' },
  fileIcon: { type: String, default: 'mdi-language-markdown' },
  fileIconColor: { type: String, default: 'info' },
  folderIcon: { type: String, default: 'mdi-folder' },
  folderOpenIcon: { type: String, default: 'mdi-folder-open' }
})

const emit = defineEmits(['select', 'create', 'rename', 'remove', 'move'])

const localNodes = ref([])
const filterText = ref('')

const expandedIds = ref(new Set())
const EXPANDED_KEY = computed(() => `markdown-collab-expanded-${props.workspaceId}`)

function persistExpanded() {
  try {
    localStorage.setItem(EXPANDED_KEY.value, JSON.stringify(Array.from(expandedIds.value)))
  } catch {}
}

function restoreExpanded() {
  try {
    const raw = localStorage.getItem(EXPANDED_KEY.value)
    if (!raw) {
      // Default: expand top-level folders for first-time users
      expandedIds.value = new Set(
        (localNodes.value || [])
          .filter(n => n.type === 'folder')
          .map(n => Number(n.id))
      )
      return
    }
    const ids = JSON.parse(raw)
    if (Array.isArray(ids)) expandedIds.value = new Set(ids.map(Number))
  } catch {}
}

watch(
  () => props.nodes,
  (val) => {
    localNodes.value = JSON.parse(JSON.stringify(val || []))
    restoreExpanded()
  },
  { immediate: true }
)

const dragEnabled = computed(() => props.canEdit && filterText.value.trim().length === 0)

function toggleExpand(id) {
  const next = new Set(expandedIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  expandedIds.value = next
  persistExpanded()
}

function findNodeById(nodes, id) {
  for (const n of nodes) {
    if (n.id === id) return n
    if (n.children?.length) {
      const found = findNodeById(n.children, id)
      if (found) return found
    }
  }
  return null
}

function filterTree(nodes, query) {
  const q = query.trim().toLowerCase()
  if (!q) return nodes
  const out = []
  for (const n of nodes) {
    const children = n.children?.length ? filterTree(n.children, query) : []
    const match = (n.title || '').toLowerCase().includes(q)
    if (match || children.length) out.push({ ...n, children })
  }
  return out
}

const filteredNodes = computed(() => filterTree(localNodes.value, filterText.value))

function emitMove(evt, parentId) {
  const moved = evt?.moved
  const added = evt?.added
  const element = moved?.element || added?.element
  const newIndex = moved?.newIndex ?? added?.newIndex
  if (!element || typeof newIndex !== 'number') return
  emit('move', { id: element.id, parentId: parentId ?? null, orderIndex: newIndex })
}

// Create dialog state
const createDialog = ref(false)
const createType = ref('file')
const createParentId = ref(null)
const createTitle = ref('')
const createError = ref('')

const createParentLabel = computed(() => {
  if (!createParentId.value) return 'Workspace Root'
  const node = findNodeById(localNodes.value, createParentId.value)
  return node ? node.title : `#${createParentId.value}`
})

const canSubmitCreate = computed(() => createTitle.value.trim().length > 0 && props.canEdit)

function openCreateDialog(type, explicitParentId = null) {
  createError.value = ''
  createType.value = type

  const selectedNode = props.selectedId ? findNodeById(localNodes.value, props.selectedId) : null
  let parentId = explicitParentId

  if (!parentId && selectedNode) {
    if (selectedNode.type === 'folder') parentId = selectedNode.id
    else parentId = selectedNode.parent_id ?? null
  }

  createParentId.value = parentId ?? null
  createTitle.value = type === 'folder' ? 'New Folder' : 'new.md'
  createDialog.value = true
}

function submitCreate() {
  if (!canSubmitCreate.value) return
  emit('create', { parentId: createParentId.value, type: createType.value, title: createTitle.value.trim() })
  createDialog.value = false
}

// Rename dialog state
const renameDialog = ref(false)
const pendingRename = ref(null)
const renameTitle = ref('')
const renameError = ref('')
const canSubmitRename = computed(() => props.canEdit && renameTitle.value.trim().length > 0)

function openRenameDialog(node) {
  renameError.value = ''
  pendingRename.value = node
  renameTitle.value = node.title
  renameDialog.value = true
}

function submitRename() {
  if (!pendingRename.value || !canSubmitRename.value) return
  emit('rename', { id: pendingRename.value.id, parentId: pendingRename.value.parent_id ?? null, title: renameTitle.value.trim() })
  renameDialog.value = false
}

// Delete dialog state
const deleteDialog = ref(false)
const pendingDelete = ref(null)

function openDeleteDialog(node) {
  pendingDelete.value = node
  deleteDialog.value = true
}

function submitDelete() {
  if (!pendingDelete.value || !props.canEdit) return
  emit('remove', { id: pendingDelete.value.id })
  deleteDialog.value = false
}
</script>

<style scoped>
.tree-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.tree-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  padding: 8px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
  min-height: 44px;
}

.header-icon {
  flex-shrink: 0;
}

.header-title {
  font-weight: 500;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
  flex: 1;
}

.header-actions {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  margin-left: auto;
}

.header-actions .v-btn {
  width: 28px !important;
  height: 28px !important;
  min-width: 28px !important;
}

.search-container {
  padding: 8px;
  flex-shrink: 0;
}

.tree-body {
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.tree-scroll {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
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
  flex-shrink: 0;
}

.drag-wrapper:hover .drag-handle {
  opacity: 0.9;
}

.tree-search :deep(.v-field__outline) {
  opacity: 0.9;
}

/* Responsive: Hide title when very narrow */
@container (max-width: 120px) {
  .header-title {
    display: none;
  }
}
</style>
