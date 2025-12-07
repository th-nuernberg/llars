<!-- PromptEngineering/PromptEngineeringDetail.vue -->
<template>
  <div class="layout-container">
    <sidebar
      :users="users"
      :blocks="blocks"
      :prompt-id="Number(promptId)"
      :is-owner="promptOwner === username"
      :shared-with="sharedWithUsers"
      :owner="promptOwner"
      :promptName="promptName"
      @showAddBlockDialog="showAddBlockDialog = true"
      @refreshPromptDetails="fetchPromptDetails()"
      @uploadJsonFileSelected="onJsonFileSelected"
      @triggerTestPrompt="openTestPromptDialog"
    />

    <div class="main-content">
      <!-- Skeleton Loading -->
      <v-skeleton-loader v-if="isLoading('prompt')" type="heading, card@3"></v-skeleton-loader>

      <template v-else>
      <h1 class="prompt-title">{{ promptName }}</h1>

      <!-- Dialog-Fenster zum Eingeben des neuen Blocknamens -->
      <div v-if="showAddBlockDialog" class="dialog-overlay">
        <div class="dialog-box">
          <h3>Neuen Block erstellen</h3>
          <input
            v-model="newBlockName"
            @keyup.enter="handleCreateBlock"
            type="text"
            placeholder="Blockname"
            class="block-input"
          />
          <div class="dialog-buttons">
            <button class="success-button" @click="handleCreateBlock">Erstellen</button>
            <button class="cancel-button" @click="closeAddBlockDialog">Abbrechen</button>
          </div>
        </div>
      </div>

      <!-- Dialog-Fenster zum Löschen eines Blocks -->
      <div v-if="showDeleteBlockDialog" class="dialog-overlay">
        <div class="dialog-box">
          <h3>Block "{{ blockToDelete?.title }}" löschen?</h3>
          <p>Soll der Block wirklich entfernt werden?</p>
          <div class="dialog-buttons">
            <button class="danger-button" @click="handleConfirmDeleteBlock">Löschen</button>
            <button class="cancel-button" @click="closeDeleteBlockDialog">Abbrechen</button>
          </div>
        </div>
      </div>

      <!-- Dialog-Fenster für die Wahl, ob Blocks überschrieben oder angehängt werden -->
      <div v-if="showUploadChoiceDialog" class="dialog-overlay">
        <div class="dialog-box">
          <h3>JSON-Blocks hochladen</h3>
          <p>Sollen die vorhandenen Blöcke überschrieben oder neue Blocks nur angehängt werden?</p>
          <div class="dialog-buttons">
            <button class="danger-button" @click="handleOverrideJsonBlocks">
              Überschreiben
            </button>
            <button class="success-button" @click="handleAppendJsonBlocks">
              Anhängen
            </button>
            <button class="cancel-button" @click="closeUploadChoiceDialog">
              Abbrechen
            </button>
          </div>
        </div>
      </div>

      <!-- Snackbar -->
      <div v-if="showSnackbar" class="snackbar">
        {{ snackbarMessage }}
      </div>

      <draggable
        v-model="sortedBlocks"
        item-key="id"
        handle=".drag-handle"
        @end="onDragEnd"
        class="draggable-container"
      >
        <template #item="{ element: block }">
          <div class="editor-block">
            <div class="editor-header">
              <div class="drag-handle">⋮⋮</div>

              <!-- If this block is being edited, show an <input>, else show the <h3> -->
              <template v-if="editingBlockId === block.id">
                <input
                  class="block-title-input"
                  type="text"
                  v-model="editingBlockTitle"
                  @keyup.enter="handleSaveBlockTitle(block)"
                  @blur="handleSaveBlockTitle(block)"
                  :placeholder="`Blocktitel ändern...`"
                />
              </template>
              <template v-else>
                <!-- Double-click or click an edit icon to start editing -->
                <h3 @dblclick="startEditBlockTitle(block)">{{ block.title }}</h3>

                <!-- Container für die Buttons -->
                <div class="header-actions">
                  <!-- Edit Button -->
                  <button
                    class="edit-title-button"
                    @click="startEditBlockTitle(block)"
                    title="Titel bearbeiten"
                  >
                    <v-icon size="small">mdi-pencil</v-icon>
                  </button>

                  <!-- Delete Button -->
                  <button
                    class="delete-button"
                    @click="openDeleteBlockDialog(block)"
                    title="Block löschen"
                  >
                    ✕
                  </button>
                </div>
              </template>
            </div>

            <!-- Editor-Inhalt -->
            <div :ref="el => setEditorRef(el, block.id)" class="editor"></div>
          </div>
        </template>
      </draggable>

      <!-- Debug-Ausgabe -->
      <div v-if="isDevelopment" class="debug-info">
        <h4>Debug Information:</h4>
        <pre>{{ JSON.stringify(blocks, null, 2) }}</pre>
      </div>
      </template>
    </div>
  </div>

  <!-- Dialog zum Testen des gesamten Prompts -->
  <TestPromptDialog v-model="showTestPromptDialog" :prompt="assemblePrompt()" />
</template>

<script>
// Modul-Script: Registrierung von Quill-Erweiterungen nur einmal
import Quill from 'quill';
import QuillCursors from 'quill-cursors';
import Inline from 'quill/blots/inline';

// Register the cursors module
Quill.register('modules/cursors', QuillCursors);
// Register custom highlight blot for placeholders
class HighlightBlot extends Inline {}
HighlightBlot.blotName = 'highlight';
HighlightBlot.tagName = 'span';
HighlightBlot.className = 'placeholder-highlight';
Quill.register(HighlightBlot);
</script>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import TestPromptDialog from './TestPromptDialog.vue';
import { useRoute } from 'vue-router';
import 'quill/dist/quill.snow.css';
import draggable from 'vuedraggable';
import sidebar from "@/components/PromptEngineering/sidebar.vue";
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';

// Composables
import { useSnackbar } from './composables/useSnackbar';
import { useDialogs } from './composables/useDialogs';
import { usePromptDetails } from './composables/usePromptDetails';
import { useYjsCollaboration } from './composables/useYjsCollaboration';
import { usePromptBlocks } from './composables/usePromptBlocks';
import { useQuillEditor } from './composables/useQuillEditor';

const isDevelopment = import.meta.env.VITE_PROJECT_STATE === 'development';

const route = useRoute();
const promptId = computed(() => route.params.id || 1);
const roomId = computed(() => `room_${promptId.value}`);
const username = localStorage.getItem('username') || 'Unbekannter Benutzer';

// Skeleton Loading
const { isLoading, setLoading, withLoading } = useSkeletonLoading(['prompt']);

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

// YJS and Socket.IO setup
const collaboration = useYjsCollaboration(
  roomId,
  username,
  () => processYDoc(),
  (userId, cursor) => updateCursor(userId, cursor)
);

const { ydoc, socket, users } = collaboration;

// Blocks management
const blocksManager = usePromptBlocks(ydoc, roomId, socket, showMessage);
const { blocks, sortedBlocks, processYDoc, createBlock, deleteBlock, saveBlockTitle, handleJsonUpload, assemblePrompt } = blocksManager;

// Quill editor management
const editorManager = useQuillEditor(ydoc, socket, roomId);
const {
  setEditorRef,
  updateCursor,
  initializeEditor,
  cleanupEditor,
  cleanupAll,
  applyHighlightingToAll,
  removeCursorForUser,
  editors
} = editorManager;

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

// Watch für neue/gelöschte Blocks
watch(
  () => blocks.value,
  async (newBlocks, oldBlocks) => {
    // Cleanup alte Editoren für gelöschte Blöcke
    if (oldBlocks) {
      const deletedBlocks = oldBlocks.filter(
        oldBlock => !newBlocks.find(newBlock => newBlock.id === oldBlock.id)
      );

      deletedBlocks.forEach(block => {
        cleanupEditor(block.id);
      });
    }

    // Initialisiere neue Editoren
    for (const block of newBlocks) {
      if (!editors.value.has(block.id)) {
        await nextTick();
        await initializeEditor(block);
      }
    }
  },
  { deep: true }
);

// Lifecycle hooks
onMounted(async () => {
  await withLoading('prompt', async () => {
    await fetchPromptDetails();
    collaboration.initialize();

    // Apply highlighting after editors are initialized
    watch(
      () => blocks.value.length,
      () => {
        applyHighlightingToAll();
      }
    );
  });
});

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
.editor-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.users-list {
  margin-bottom: 20px;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.user-item {
  display: flex;
  align-items: center;
  margin: 5px 0;
}

.user-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 8px;
}

.editor-block {
  margin-bottom: 30px;
}

.editor-block h3 {
  margin-bottom: 10px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
}

.debug-info {
  margin-top: 20px;
  padding: 10px;
  background: #f5f5f5;
  border-radius: 4px;
}

.debug-info pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}

.editor {
  min-height: 150px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: #fff;
}

:deep(.ql-container) {
  font-size: 16px;
}

:deep(.ql-editor) {
  min-height: 100px;
  padding: 15px;
}

:deep(.ql-cursor) {
  display: block;
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
}

:deep(.ql-cursor-flag) {
  display: inline-flex;
  align-items: center;
  position: absolute;
  padding: 3px 5px;
  border-radius: 3px;
  font-size: 12px;
  color: white;
  white-space: nowrap;
  transform: translate(-50%, -100%);
  z-index: 1;
}

:deep(.ql-cursor-caret) {
  position: absolute;
  margin-top: -1px;
  width: 2px;
}

:deep(.ql-cursor-selection) {
  position: absolute;
  pointer-events: none;
  opacity: 0.3;
}
.add-block-button {
  margin-bottom: 20px;
  padding: 8px 12px;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.dialog-box {
  background: white;
  padding: 24px;
  border-radius: 8px;
  min-width: 320px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

/* Platzhalter-Hervorhebung in Quill-Editor */
:deep(.placeholder-highlight) {
  background-color: #fff176; /* sanftes Gelb */
  padding: 0 2px;
  border-radius: 2px;
  border: 1px solid #ffd600;
  display: inline-block;
  font-weight: 500;
}

.dialog-box h3 {
  margin: 0 0 16px 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a1a1a;
}

.dialog-box p {
  margin: 0 0 20px 0;
  color: #4b5563;
  font-size: 0.95rem;
  line-height: 1.5;
}

.block-input {
  width: 100%;
  margin: 10px 0;
  padding: 8px;
}

.dialog-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* Button-Grundstil - kann bei Bedarf angepasst werden */
.dialog-buttons button {
  padding: 8px 14px;
  border: none;
  border-radius: 16px 4px 16px 4px;  /* Wie in der Sidebar */
  cursor: pointer;
  min-height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Für "Abbrechen"-Button (neutral/grau) */
.dialog-buttons .cancel-button {
  background-color: #9e9e9e;  /* Gleiche Farbe wie back-button */
  color: #fff;
  transition: background-color 0.2s;
}
.dialog-buttons .cancel-button:hover {
  background-color: #7e7e7e;
}

/* Für "Erstellen"/"Hinzufügen" (grün) */
.dialog-buttons .success-button {
  background-color: #4caf50;  /* Gleiche Farbe wie add-block-button */
  color: #fff;
  transition: background-color 0.2s;
}
.dialog-buttons .success-button:hover {
  background-color: #45a049;
}

/* Für "Löschen" (rot) */
.dialog-buttons .danger-button {
  background-color: #e74c3c;
  color: #fff;
  transition: background-color 0.2s;
}
.dialog-buttons .danger-button:hover {
  background-color: #c0392b;
}


.snackbar {
  position: fixed;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%);
  background: #323232;
  color: white;
  padding: 12px 20px;
  border-radius: 6px;
  font-size: 0.9rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
  z-index: 9999;
  opacity: 0;
  pointer-events: none;
  text-align: center;
  animation: snackbar 3s ease-in-out forwards;
}

@keyframes snackbar {
  0% {
    opacity: 0;
    transform: translate(-50%, 20px);
  }
  15% {
    opacity: 1;
    transform: translate(-50%, 0);
  }
  85% {
    opacity: 1;
    transform: translate(-50%, 0);
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -20px);
  }
}

@keyframes fadein {
  from { opacity: 0; }
  to   { opacity: 1; }
}

.layout-container {
  display: flex;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  margin-left: 250px; /* Entspricht der Sidebar-Breite */
  padding: 20px;
  max-width: calc(100% - 250px);
}

.prompt-title {
  font-size: 1.75rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 1.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #eee;
}

.draggable-container {
  width: 100%;
}

.editor-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

/* Drag-Handle */
.drag-handle {
  cursor: move;
  padding: 5px;
  color: #666;
  user-select: none;
}

.drag-handle:hover {
  color: #333;
}

/* Card-Styling */
.editor-block {
  margin-bottom: 30px;
  padding: 15px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.block-title-input {
  font-size: 1.1rem;
  padding: 4px 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  flex: 1; /* So it takes up available horizontal space if you prefer */
}

.header-actions {
  margin-left: auto; /* Buttons ganz rechts platzieren */
  display: flex;
  gap: 8px; /* Abstand zwischen den Buttons */
}

.edit-title-button {
  padding: 4px;
  color: grey;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.9);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  width: 24px;
  height: 24px;
}

.edit-title-button:hover {
  background: rgba(255, 255, 255, 1);
  color: #6ca077;
}

.delete-button {
  padding: 4px;
  color: grey;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.9);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  width: 24px;
  height: 24px;
}

.delete-button:hover {
  background: rgba(255, 255, 255, 1);
  color: #e74c3c;
}
/* Styles für Test Prompt Dialog */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.dialog-box.test-prompt-dialog {
  background: white;
  padding: 24px;
  border-radius: 8px;
  max-width: 80%;
  max-height: 80%;
  overflow: auto;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.response-stream {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  max-height: 300px;
  overflow: auto;
  white-space: pre-wrap;
  margin-bottom: 12px;
}
.stream-indicator {
  margin-top: 8px;
  font-weight: bold;
}

/* QoL: Toggle-Button für komprimiertes Prompt */
.toggle-button {
  background: none;
  border: none;
  color: #3498db;
  cursor: pointer;
  margin-bottom: 12px;
  padding: 0;
}
.toggle-button:hover {
  text-decoration: underline;
}

</style>
