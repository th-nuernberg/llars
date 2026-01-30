<template>
  <div class="tree-panel">
    <div v-if="!hideHeader" class="tree-header">
      <LIcon size="20" class="header-icon">mdi-file-tree</LIcon>
      <span class="header-title">{{ $t('markdownCollab.tree.title') }}</span>
      <div class="header-actions">
        <v-btn
          icon
          variant="text"
          size="x-small"
          :disabled="!canEdit"
          :title="$t('markdownCollab.tree.actions.newFile')"
          @click="openCreateDialog('file')"
        >
          <LIcon size="18">file-plus</LIcon>
        </v-btn>
        <v-btn
          icon
          variant="text"
          size="x-small"
          :disabled="!canEdit"
          :title="$t('markdownCollab.tree.actions.newFolder')"
          @click="openCreateDialog('folder')"
        >
          <LIcon size="18">folder-plus</LIcon>
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
        :placeholder="$t('markdownCollab.tree.searchPlaceholder')"
        prepend-inner-icon="mdi-magnify"
        class="tree-search"
      />
    </div>

    <div class="tree-body">
      <v-skeleton-loader v-if="loading" type="list-item@10" class="px-3 pt-2" />

      <div v-else class="tree-scroll">
        <MarkdownTreeNode
          v-for="(node, index) in displayNodes"
          :key="node.id"
          :node="node"
          :selected-id="selectedId"
          :expanded-ids="expandedIds"
          :can-edit="canEdit"
          :drag-enabled="dragEnabled"
          :recently-added-ids="recentlyAddedIds"
          :file-icon="fileIcon"
          :file-icon-color="fileIconColor"
          :folder-icon="folderIcon"
          :folder-open-icon="folderOpenIcon"
          :sibling-index="index"
          :sibling-count="displayNodes.length"
          @select="$emit('select', $event)"
          @toggle="toggleExpand"
          @create="(p) => openCreateDialog(p.type, p.parentId)"
          @rename="openRenameDialog"
          @remove="openDeleteDialog"
          @move="$emit('move', $event)"
        />
        <!-- Drop zone at END of root level -->
        <div
          v-if="dragEnabled && displayNodes.length > 0"
          class="root-drop-end"
          @dragover.prevent="onRootDragOver"
          @dragleave="onRootDragLeave"
          @drop="onRootDrop"
          :class="{ active: rootDropActive }"
        />
      </div>
    </div>

    <!-- Create -->
    <v-dialog v-model="createDialog" max-width="520">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon class="mr-2">{{ createType === 'folder' ? 'folder-plus' : 'file-plus' }}</LIcon>
          {{ createType === 'folder' ? $t('markdownCollab.tree.dialogs.createFolderTitle') : $t('markdownCollab.tree.dialogs.createFileTitle') }}
          <v-spacer />
          <LIconBtn icon="mdi-close" :tooltip="$t('common.close')" @click="createDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-alert v-if="createError" type="error" variant="tonal" class="mb-4">
            {{ createError }}
          </v-alert>
          <v-text-field
            v-model="createTitle"
            :label="$t('markdownCollab.tree.dialogs.nameLabel')"
            :placeholder="createType === 'folder' ? folderPlaceholderText : filePlaceholderText"
            variant="outlined"
            density="comfortable"
            autofocus
          />
          <div class="text-caption text-medium-emphasis">
            {{ $t('markdownCollab.tree.dialogs.target', { label: createParentLabel }) }}
          </div>
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" :title="$t('markdownCollab.tree.actions.cancelCreate')" @click="createDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" :title="$t('markdownCollab.tree.actions.create')" :disabled="!canSubmitCreate" @click="submitCreate">
            {{ $t('markdownCollab.tree.actions.createLabel') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Rename -->
    <v-dialog v-model="renameDialog" max-width="520">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon class="mr-2">mdi-rename-box</LIcon>
          {{ $t('markdownCollab.tree.dialogs.renameTitle') }}
          <v-spacer />
          <LIconBtn icon="mdi-close" :tooltip="$t('common.close')" @click="renameDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-alert v-if="renameError" type="error" variant="tonal" class="mb-4">
            {{ renameError }}
          </v-alert>
          <v-text-field
            v-model="renameTitle"
            :label="$t('markdownCollab.tree.dialogs.nameLabel')"
            variant="outlined"
            density="comfortable"
            autofocus
          />
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" :title="$t('markdownCollab.tree.actions.cancelRename')" @click="renameDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" :title="$t('markdownCollab.tree.actions.save')" :disabled="!canSubmitRename" @click="submitRename">
            {{ $t('common.save') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete -->
    <v-dialog v-model="deleteDialog" max-width="520">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon class="mr-2" color="error">mdi-delete-outline</LIcon>
          {{ $t('markdownCollab.tree.dialogs.deleteTitle') }}
          <v-spacer />
          <LIconBtn icon="mdi-close" :tooltip="$t('common.close')" @click="deleteDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text>
          <i18n-t keypath="markdownCollab.tree.dialogs.deleteConfirm" tag="div" class="text-body-1">
            <template #name>
              <strong>{{ pendingDelete?.title }}</strong>
            </template>
          </i18n-t>
          <div class="text-caption text-medium-emphasis mt-2">
            {{ $t('markdownCollab.tree.dialogs.deleteHint') }}
          </div>
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" :title="$t('markdownCollab.tree.actions.cancelDelete')" @click="deleteDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="error" :title="$t('markdownCollab.tree.actions.delete')" @click="submitDelete">{{ $t('common.delete') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import MarkdownTreeNode from './MarkdownTreeNode.vue'

const props = defineProps({
  workspaceId: { type: Number, required: true },
  nodes: { type: Array, default: () => [] },
  selectedId: { type: Number, default: null },
  loading: { type: Boolean, default: false },
  canEdit: { type: Boolean, default: false },
  recentlyAddedIds: { type: Set, default: () => new Set() },
  filePlaceholder: { type: String, default: '' },
  fileIcon: { type: String, default: 'mdi-language-markdown' },
  fileIconColor: { type: String, default: 'info' },
  folderIcon: { type: String, default: 'mdi-folder' },
  folderOpenIcon: { type: String, default: 'mdi-folder-open' },
  hideHeader: { type: Boolean, default: false }
})

const emit = defineEmits(['select', 'create', 'rename', 'remove', 'move'])

const { t } = useI18n()

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
const filePlaceholderText = computed(() => props.filePlaceholder || t('markdownCollab.tree.placeholders.file'))
const folderPlaceholderText = computed(() => t('markdownCollab.tree.placeholders.folder'))

// Root drop zone state
const rootDropActive = ref(false)

function onRootDragOver(e) {
  e.preventDefault()
  rootDropActive.value = true
  e.dataTransfer.dropEffect = 'move'
}

function onRootDragLeave() {
  rootDropActive.value = false
}

function onRootDrop(e) {
  e.preventDefault()
  rootDropActive.value = false

  if (!dragEnabled.value) return

  try {
    const data = JSON.parse(e.dataTransfer.getData('text/plain'))
    // Drop at end of root level
    emit('move', {
      id: data.id,
      parentId: null,
      orderIndex: displayNodes.value.length
    })
  } catch (err) {
    console.error('Root drop error:', err)
  }
}

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

// Use filtered nodes when searching, otherwise use localNodes for drag-and-drop
const displayNodes = computed(() => {
  if (filterText.value.trim().length > 0) {
    return filteredNodes.value
  }
  return localNodes.value
})

// Create dialog state
const createDialog = ref(false)
const createType = ref('file')
const createParentId = ref(null)
const createTitle = ref('')
const createError = ref('')

const createParentLabel = computed(() => {
  if (!createParentId.value) return t('markdownCollab.tree.root')
  const node = findNodeById(localNodes.value, createParentId.value)
  return node ? node.title : t('markdownCollab.tree.nodeFallback', { id: createParentId.value })
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
  createTitle.value = type === 'folder'
    ? t('markdownCollab.tree.defaults.folder')
    : t('markdownCollab.tree.defaults.file')
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

// Expose functions for parent components
defineExpose({ openCreateDialog })
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
  padding: 4px 8px;
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

/* Root drop zone at end of tree */
.root-drop-end {
  height: 20px;
  margin: 4px 8px;
  position: relative;
  cursor: default;
}

.root-drop-end::after {
  content: '';
  position: absolute;
  left: 4px;
  right: 4px;
  top: 50%;
  height: 3px;
  transform: translateY(-50%);
  border-radius: 2px;
  background: transparent;
  transition: all 0.1s ease;
}

.root-drop-end.active::after {
  background: var(--llars-primary, #b0ca97);
  box-shadow: 0 0 6px rgba(176, 202, 151, 0.6);
}
</style>
