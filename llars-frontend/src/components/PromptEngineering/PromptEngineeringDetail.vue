<!-- PromptEngineering/PromptEngineeringDetail.vue -->
<template>
  <div
    ref="containerRef"
    class="prompt-workspace"
    :class="{ 'prompt-workspace--git-hidden': !showGitPanel }"
  >
    <!-- Left Panel: Sidebar -->
    <div class="left-panel" :style="leftPanelStyle()">
      <sidebar
        :users="users"
        :blocks="blocks"
        :prompt-id="Number(promptId)"
        :is-owner="promptOwner === username"
        :shared-with="sharedWithUsers"
        :owner="promptOwner"
        :promptName="promptName"
        :show-git-panel="showGitPanel"
        @showAddBlockDialog="showAddBlockDialog = true"
        @refreshPromptDetails="fetchPromptDetails()"
        @uploadJsonFileSelected="onJsonFileSelected"
        @triggerTestPrompt="openTestPromptDialog"
        @toggleGitPanel="toggleGitPanel"
      />
    </div>

    <!-- Resize Divider -->
    <div
      class="resize-divider"
      :class="{ resizing: isResizing }"
      @mousedown="startResize"
    >
      <div class="resize-handle"></div>
    </div>

    <!-- Right Panel: Editor -->
    <div class="right-panel" :style="rightPanelStyle()">
      <!-- Loading State -->
      <div v-if="isLoading('prompt')" class="loading-state">
        <v-skeleton-loader type="heading" class="mb-4" />
        <v-skeleton-loader type="card" class="mb-4" />
        <v-skeleton-loader type="card" class="mb-4" />
        <v-skeleton-loader type="card" />
      </div>

      <template v-else>
        <!-- Prompt Header -->
        <div class="prompt-header">
          <h1 class="prompt-title">{{ promptName }}</h1>
          <div class="prompt-meta">
            <LTag variant="primary" size="small">
              {{ blocks.length }} {{ blocks.length === 1 ? 'Block' : 'Blöcke' }}
            </LTag>
            <span v-if="sharedWithUsers.length" class="text-caption text-medium-emphasis ml-2">
              <v-icon size="14" class="mr-1">mdi-share-variant</v-icon>
              {{ sharedWithUsers.length }} Nutzer
            </span>
          </div>
        </div>

        <!-- Blocks Container -->
        <div ref="blocksContainerRef" class="blocks-container">
          <draggable
            v-if="blocks.length > 0"
            v-model="sortedBlocks"
            item-key="id"
            handle=".drag-handle"
            @end="onDragEnd"
            class="draggable-container"
          >
            <template #item="{ element: block }">
              <div class="editor-block">
                <div class="editor-header">
                  <div class="drag-handle" title="Ziehen um zu sortieren">
                    <v-icon size="18">mdi-drag</v-icon>
                  </div>

                  <!-- Block Title -->
                  <template v-if="editingBlockId === block.id">
                    <input
                      class="block-title-input"
                      type="text"
                      v-model="editingBlockTitle"
                      @keyup.enter="handleSaveBlockTitle(block)"
                      @blur="handleSaveBlockTitle(block)"
                      @keyup.escape="resetBlockTitleEdit"
                      placeholder="Blocktitel..."
                      autofocus
                    />
                  </template>
                  <template v-else>
                    <h3 class="block-title" @dblclick="startEditBlockTitle(block)">
                      {{ block.title }}
                    </h3>
                  </template>

                  <v-spacer />

                  <div class="header-actions">
                    <v-btn
                      icon
                      variant="text"
                      size="x-small"
                      @click="startEditBlockTitle(block)"
                      title="Umbenennen"
                    >
                      <v-icon size="16">mdi-pencil</v-icon>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="x-small"
                      color="error"
                      @click="openDeleteBlockDialog(block)"
                      title="Löschen"
                    >
                      <v-icon size="16">mdi-delete</v-icon>
                    </v-btn>
                  </div>
                </div>

                <!-- Quill Editor -->
                <div :ref="el => setEditorRef(el, block)" class="editor-content"></div>
              </div>
            </template>
          </draggable>

          <!-- Empty State -->
          <div v-else class="empty-blocks">
            <v-icon size="48" color="grey-lighten-1">mdi-file-document-plus-outline</v-icon>
            <div class="text-subtitle-1 mt-3">Noch keine Blöcke</div>
            <div class="text-body-2 text-medium-emphasis mb-4">
              Erstellen Sie Ihren ersten Prompt-Block.
            </div>
            <LBtn variant="accent" prepend-icon="mdi-plus" @click="showAddBlockDialog = true">
              Neuer Block
            </LBtn>
          </div>
        </div>

        <!-- Git Panel -->
        <div v-if="showGitPanel" ref="gitPanelRef" class="mt-4">
          <PromptGitPanel
            :prompt-id="Number(promptId)"
            :summary="gitSummary"
            :can-commit="true"
            :get-content="getContentSnapshot"
            @committed="onGitCommitted"
          />
        </div>

        <!-- Debug Info (Development only) -->
        <div v-if="isDevelopment" class="debug-info">
          <h4>Debug Information:</h4>
          <pre>{{ JSON.stringify(blocks, null, 2) }}</pre>
        </div>
      </template>
    </div>

    <!-- Add Block Dialog -->
    <v-dialog v-model="showAddBlockDialog" max-width="440">
      <LCard>
        <template #header>
          <div class="d-flex align-center w-100">
            <v-icon class="mr-2" color="accent">mdi-plus-circle</v-icon>
            <span class="text-h6">Neuen Block erstellen</span>
          </div>
        </template>

        <v-text-field
          v-model="newBlockName"
          label="Blockname"
          placeholder="z. B. Systemanweisung, Kontext, ..."
          variant="outlined"
          density="comfortable"
          autofocus
          @keyup.enter="handleCreateBlock"
        />

        <template #actions>
          <v-spacer />
          <LBtn variant="cancel" @click="closeAddBlockDialog">Abbrechen</LBtn>
          <LBtn variant="accent" :disabled="!newBlockName?.trim()" @click="handleCreateBlock">
            Erstellen
          </LBtn>
        </template>
      </LCard>
    </v-dialog>

    <!-- Delete Block Dialog -->
    <v-dialog v-model="showDeleteBlockDialog" max-width="400">
      <LCard>
        <template #header>
          <div class="d-flex align-center w-100">
            <v-icon class="mr-2" color="error">mdi-delete-alert</v-icon>
            <span class="text-h6">Block löschen</span>
          </div>
        </template>

        <p class="text-body-1">
          Möchten Sie den Block <strong>"{{ blockToDelete?.title }}"</strong> wirklich löschen?
        </p>
        <p class="text-body-2 text-medium-emphasis">
          Diese Aktion kann nicht rückgängig gemacht werden.
        </p>

        <template #actions>
          <v-spacer />
          <LBtn variant="cancel" @click="closeDeleteBlockDialog">Abbrechen</LBtn>
          <LBtn variant="danger" @click="handleConfirmDeleteBlock">Löschen</LBtn>
        </template>
      </LCard>
    </v-dialog>

    <!-- Upload Choice Dialog -->
    <v-dialog v-model="showUploadChoiceDialog" max-width="440">
      <LCard>
        <template #header>
          <div class="d-flex align-center w-100">
            <v-icon class="mr-2" color="secondary">mdi-upload</v-icon>
            <span class="text-h6">JSON importieren</span>
          </div>
        </template>

        <p class="text-body-1">
          Wie sollen die importierten Blöcke eingefügt werden?
        </p>

        <template #actions>
          <v-spacer />
          <LBtn variant="cancel" @click="closeUploadChoiceDialog">Abbrechen</LBtn>
          <LBtn variant="danger" @click="handleOverrideJsonBlocks">Überschreiben</LBtn>
          <LBtn variant="primary" @click="handleAppendJsonBlocks">Anhängen</LBtn>
        </template>
      </LCard>
    </v-dialog>

    <!-- Test Prompt Dialog -->
    <TestPromptDialog v-model="showTestPromptDialog" :prompt="assemblePrompt()" />

    <!-- Snackbar -->
    <v-snackbar v-model="showSnackbar" :timeout="3000" color="success">
      {{ snackbarMessage }}
    </v-snackbar>
  </div>
</template>

<script>
// Module script: Register Quill extensions once
import Quill from 'quill';
import QuillCursors from 'quill-cursors';
import Inline from 'quill/blots/inline';

Quill.register('modules/cursors', QuillCursors);

class HighlightBlot extends Inline {}
HighlightBlot.blotName = 'highlight';
HighlightBlot.tagName = 'span';
HighlightBlot.className = 'placeholder-highlight';
Quill.register(HighlightBlot);

class UserHighlightBlot extends Inline {
  static create(value) {
    const node = super.create();
    if (value) {
      node.style.setProperty('--llars-collab-bg', value);
    }
    return node;
  }

  static formats(node) {
    return node.style.getPropertyValue('--llars-collab-bg') || null;
  }
}
UserHighlightBlot.blotName = 'llars-user-highlight';
UserHighlightBlot.tagName = 'span';
UserHighlightBlot.className = 'llars-user-highlight';
Quill.register(UserHighlightBlot);
</script>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import TestPromptDialog from './TestPromptDialog.vue';
import PromptGitPanel from './PromptGitPanel.vue';
import { useRoute } from 'vue-router';
import 'quill/dist/quill.snow.css';
import draggable from 'vuedraggable';
import sidebar from "@/components/PromptEngineering/sidebar.vue";
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';
import { usePanelResize } from '@/composables/usePanelResize';

// Composables
import { useSnackbar } from './composables/useSnackbar';
import { useDialogs } from './composables/useDialogs';
import { usePromptDetails } from './composables/usePromptDetails';
import { useYjsCollaboration } from './composables/useYjsCollaboration';
import { usePromptBlocks } from './composables/usePromptBlocks';
import { useQuillEditor } from './composables/useQuillEditor';
import { usePromptGitDiff } from './composables/usePromptGitDiff';
import { useAuth } from '@/composables/useAuth';
import { useActiveDuration, useScrollDepth, useTypingMetrics, useVisibilityTracker } from '@/composables/useAnalyticsMetrics';

const isDevelopment = import.meta.env.VITE_PROJECT_STATE === 'development';

const route = useRoute();
const promptId = computed(() => route.params.id || 1);
const roomId = computed(() => `room_${promptId.value}`);
const username = localStorage.getItem('username') || 'Unbekannter Benutzer';
const blocksContainerRef = ref(null);
const gitPanelRef = ref(null);
const promptEntity = computed(() => `prompt:${promptId.value}`);

// Skeleton Loading
const { isLoading, setLoading, withLoading } = useSkeletonLoading(['prompt']);

// Resizable Panel
const {
  isResizing,
  containerRef,
  startResize,
  leftPanelStyle,
  rightPanelStyle
} = usePanelResize({
  initialLeftPercent: 22,
  minLeftPercent: 15,
  maxLeftPercent: 40,
  storageKey: 'prompt-engineering-sidebar-width'
});

// Composables initialization
const { showSnackbar, snackbarMessage, showMessage } = useSnackbar();

const {
  showAddBlockDialog,
  newBlockName,
  closeAddBlockDialog,
  showDeleteBlockDialog,
  blockToDelete,
  openDeleteBlockDialog,
  closeDeleteBlockDialog,
  showUploadChoiceDialog,
  pendingJsonData,
  openUploadChoiceDialog,
  closeUploadChoiceDialog,
  editingBlockId,
  editingBlockTitle,
  startEditBlockTitle,
  resetBlockTitleEdit,
  showTestPromptDialog,
  openTestPromptDialog
} = useDialogs();

const { promptName, promptOwner, sharedWithUsers, fetchPromptDetails } = usePromptDetails(promptId);
const auth = useAuth();
const typingMetrics = useTypingMetrics({
  category: 'prompt',
  name: 'editor',
  dimensions: () => ({ entity: promptEntity.value, view: 'editor' })
});

useActiveDuration({
  category: 'prompt',
  action: 'session_active_ms',
  name: () => `prompt:${promptId.value}`,
  dimensions: () => ({ entity: promptEntity.value })
});

const paneVisibility = useVisibilityTracker({
  category: 'prompt',
  action: 'pane_visible_ms',
  nameBuilder: (id) => `pane:${id}`,
  dimensions: () => ({ entity: promptEntity.value })
});

useScrollDepth(blocksContainerRef, {
  category: 'prompt',
  action: 'scroll_depth',
  name: () => `prompt:${promptId.value}|editor`,
  dimensions: () => ({ entity: promptEntity.value, view: 'editor' })
});

const countDeltaChars = (delta) => {
  if (!delta?.ops) return 0;
  return delta.ops.reduce((total, op) => {
    if (typeof op.insert === 'string') return total + op.insert.length;
    if (op.insert) return total + 1;
    return total;
  }, 0);
};

// YJS and Socket.IO setup
const collaboration = useYjsCollaboration(
  roomId,
  username,
  () => processYDoc(),
  (userId, cursor) => updateCursor(userId, cursor),
  { autoSync: true }  // Enable automatic Yjs sync (sends incremental updates only)
);

const { ydoc, socket, users, updateColor } = collaboration;

// Blocks management
const blocksManager = usePromptBlocks(ydoc, roomId, socket, showMessage);
const { blocks, sortedBlocks, processYDoc, createBlock, deleteBlock, saveBlockTitle, handleJsonUpload, assemblePrompt } = blocksManager;

// Git versioning - declare early so editors can reference showGitPanel
const showGitPanel = ref(true); // Stored in localStorage
const gitDiff = usePromptGitDiff(promptId, users);

const getCurrentUserColor = () => {
  const authColor = auth.collabColor?.value || null;
  if (authColor) return authColor;

  const socketId = socket.value?.id || null;
  if (socketId && users.value?.[socketId]?.color) {
    return users.value[socketId].color;
  }

  const targetName = auth.username?.value || username;
  const userEntry = Object.values(users.value || {}).find((user) => user?.username === targetName);
  return userEntry?.color || null;
};

// Quill editor management with user highlighting support
const editorManager = useQuillEditor(ydoc, socket, roomId, {
  getUserColor: () => getCurrentUserColor(),
  getUsername: () => auth.username?.value || username,
  showUserHighlighting: () => showGitPanel.value,
  onUserTextChange: ({ delta }) => {
    const chars = countDeltaChars(delta);
    if (chars > 0) {
      typingMetrics.recordInput(chars);
    }
  }
});
const {
  editorCount,
  setEditorRef,
  updateCursor,
  cleanupEditor,
  cleanupAll,
  applyHighlightingToAll,
  removeCursorForUser,
  clearUserHighlights,
  flushPendingHighlights,
  editors
} = editorManager;
const gitSummary = ref({ users: [], insertions: 0, deletions: 0, hasChanges: false, totalChangedLines: 0 });

// Load git panel visibility from localStorage
const loadGitPanelVisibility = () => {
  try {
    const stored = localStorage.getItem('prompt-git-panel-visible');
    showGitPanel.value = stored !== 'false';
  } catch {
    showGitPanel.value = true;
  }
};

// Save git panel visibility to localStorage
const saveGitPanelVisibility = (visible) => {
  try {
    localStorage.setItem('prompt-git-panel-visible', String(visible));
  } catch {
    // Ignore
  }
};

// Toggle git panel visibility
const toggleGitPanel = () => {
  showGitPanel.value = !showGitPanel.value;
  saveGitPanelVisibility(showGitPanel.value);
};

// Get current content as snapshot string (for commits)
const getContentSnapshot = () => {
  const result = {};
  for (const block of sortedBlocks.value) {
    const editor = editors.get(block.id);
    if (editor) {
      result[block.title] = editor.getText().trim();
    } else if (block.content) {
      result[block.title] = typeof block.content === 'string' ? block.content : block.content.toString?.() || '';
    }
  }
  return JSON.stringify(result, null, 2);
};

// Update git summary when content changes
const updateGitSummary = () => {
  const currentContent = getContentSnapshot();
  const summary = gitDiff.getChangeSummary(currentContent);

  // Add current user if they made changes
  if (summary.hasChanges && auth.username?.value) {
    const existingUser = summary.users.find(u => u.username === auth.username.value);
    if (!existingUser) {
      summary.users.push({
        username: auth.username.value,
        color: auth.collabColor?.value || '#9e9e9e',
        changedLines: summary.totalChangedLines
      });
    }
  }

  gitSummary.value = summary;
};

// Handle commit completed
const onGitCommitted = () => {
  gitDiff.updateBaseline(getContentSnapshot());
  clearUserHighlights(); // Clear text highlighting after commit
  updateGitSummary();
};

// Event handlers
const handleCreateBlock = () => {
  if (createBlock(newBlockName.value)) {
    closeAddBlockDialog();
  }
};

const handleConfirmDeleteBlock = () => {
  if (deleteBlock(blockToDelete.value)) {
    closeDeleteBlockDialog();
  }
};

const handleSaveBlockTitle = (block) => {
  if (saveBlockTitle(block, editingBlockTitle.value)) {
    resetBlockTitleEdit();
  } else {
    resetBlockTitleEdit();
  }
};

const onJsonFileSelected = (jsonData) => {
  openUploadChoiceDialog(jsonData);
};

const handleOverrideJsonBlocks = () => {
  if (handleJsonUpload(pendingJsonData.value, true)) {
    closeUploadChoiceDialog();
  }
};

const handleAppendJsonBlocks = () => {
  if (handleJsonUpload(pendingJsonData.value, false)) {
    closeUploadChoiceDialog();
  }
};

const onDragEnd = () => {
  showMessage('Block-Reihenfolge aktualisiert!');
};

watch(blocksContainerRef, (el) => {
  paneVisibility.register('editor', el, { view: 'editor' });
});

watch(gitPanelRef, (el) => {
  paneVisibility.register('git', el, { view: 'git' });
});

// Watch for new/deleted blocks
watch(
  () => blocks.value,
  (newBlocks, oldBlocks) => {
    if (oldBlocks) {
      const deletedBlocks = oldBlocks.filter(
        oldBlock => !newBlocks.find(newBlock => newBlock.id === oldBlock.id)
      );
      deletedBlocks.forEach(block => {
        cleanupEditor(block.id);
      });
    }

    // Update git summary when blocks change
    updateGitSummary();
  },
  { deep: true }
);

// Debounced git summary update for text changes
let gitUpdateTimeout = null;
const debouncedGitUpdate = () => {
  if (gitUpdateTimeout) clearTimeout(gitUpdateTimeout);
  gitUpdateTimeout = setTimeout(() => {
    updateGitSummary();
  }, 500);
};

// Watch editors map for content changes
watch(
  () => editorCount.value,
  () => {
    // Re-attach text-change listeners when editors change
    for (const [blockId, editor] of editors) {
      if (!editor._gitListenerAttached) {
        editor.on('text-change', debouncedGitUpdate);
        editor._gitListenerAttached = true;
      }
    }
  }
);

// Lifecycle hooks
onMounted(async () => {
  // Load git panel visibility preference
  loadGitPanelVisibility();

  await withLoading('prompt', async () => {
    await fetchPromptDetails();
    collaboration.initialize();

    // Load git baseline for diff tracking
    await gitDiff.loadBaseline();
    updateGitSummary();

    watch(
      () => blocks.value.length,
      () => {
        applyHighlightingToAll();
      }
    );
  });
});

watch(
  () => auth.collabColor.value,
  (newColor) => {
    if (newColor && socket.value?.connected) {
      updateColor(newColor);
    }
  }
);

watch(
  [
    () => auth.collabColor.value,
    () => users.value,
    () => socket.value?.id
  ],
  () => {
    flushPendingHighlights();
  },
  { deep: true }
);

onUnmounted(() => {
  cleanupAll();
  collaboration.cleanup();
});

// User left handler
watch(users, (newUsers, oldUsers) => {
  if (oldUsers) {
    Object.keys(oldUsers).forEach(userId => {
      if (!newUsers[userId]) {
        removeCursorForUser(userId);
      }
    });
  }
});
</script>

<style scoped>
.prompt-workspace {
  height: calc(100vh - 94px);
  display: flex;
  overflow: hidden;
  background: rgb(var(--v-theme-background));
}

.left-panel {
  flex-shrink: 0;
  height: 100%;
  overflow: hidden;
}

.resize-divider {
  width: 4px;
  background: transparent;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.15s ease;
  z-index: 10;
}

.resize-divider:hover,
.resize-divider.resizing {
  background: rgba(var(--v-theme-primary), 0.2);
}

.resize-handle {
  width: 2px;
  height: 40px;
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 2px;
  transition: all 0.15s ease;
}

.resize-divider:hover .resize-handle,
.resize-divider.resizing .resize-handle {
  background: rgb(var(--v-theme-primary));
  height: 60px;
}

.right-panel {
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.loading-state {
  padding: 24px;
}

.prompt-header {
  flex-shrink: 0;
  padding: 20px 24px;
  background: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.prompt-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

.prompt-meta {
  display: flex;
  align-items: center;
}

.blocks-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.draggable-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.editor-block {
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.editor-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.drag-handle {
  cursor: grab;
  color: rgba(var(--v-theme-on-surface), 0.4);
  display: flex;
  align-items: center;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.15s ease;
}

.drag-handle:hover {
  color: rgb(var(--v-theme-on-surface));
  background: rgba(var(--v-theme-on-surface), 0.08);
}

.block-title {
  font-size: 1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
  cursor: pointer;
}

.block-title:hover {
  color: rgb(var(--v-theme-primary));
}

.block-title-input {
  flex: 1;
  font-size: 1rem;
  font-weight: 600;
  padding: 6px 10px;
  border: 1px solid rgb(var(--v-theme-primary));
  border-radius: 6px;
  background: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
  outline: none;
}

.header-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.editor-block:hover .header-actions {
  opacity: 1;
}

.editor-content {
  min-height: 180px;
  background: rgb(var(--v-theme-surface));
}

:deep(.ql-container) {
  font-size: 15px;
  border: none !important;
}

:deep(.ql-editor) {
  min-height: 150px;
  padding: 16px;
  line-height: 1.6;
}

:deep(.ql-toolbar) {
  border: none !important;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08) !important;
  background: rgba(var(--v-theme-on-surface), 0.02);
}

:deep(.placeholder-highlight) {
  background-color: #fff176;
  padding: 1px 4px;
  border-radius: 3px;
  border: 1px solid #ffd600;
  font-weight: 500;
}

:deep(.llars-user-highlight) {
  background-color: var(--llars-collab-bg);
  border-radius: 2px;
}

.prompt-workspace--git-hidden :deep(.llars-user-highlight) {
  background-color: transparent !important;
}

:deep(.ql-cursor-flag) {
  display: inline-flex;
  align-items: center;
  position: absolute;
  padding: 3px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  color: white;
  white-space: nowrap;
  transform: translate(-50%, -100%);
  z-index: 100;
}

:deep(.ql-cursor-caret) {
  position: absolute;
  margin-top: -1px;
  width: 2px;
}

.empty-blocks {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 48px 24px;
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  border: 1px dashed rgba(var(--v-theme-on-surface), 0.12);
}

.debug-info {
  margin-top: 24px;
  padding: 16px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  border-radius: 8px;
}

.debug-info h4 {
  margin: 0 0 12px 0;
  font-size: 0.9rem;
  color: rgb(var(--v-theme-on-surface));
}

.debug-info pre {
  font-size: 0.8rem;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
}

.w-100 {
  width: 100%;
}
</style>
