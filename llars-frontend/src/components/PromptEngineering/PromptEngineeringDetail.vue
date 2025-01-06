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
      @showAddBlockDialog="showAddBlockDialog = true"
      @refreshPromptDetails="fetchPromptDetails()"
    />

    <div class="main-content">
      <h1 class="prompt-title">{{ promptName }}</h1>

      <!-- Dialog-Fenster zum Eingeben des neuen Blocknamens -->
      <div v-if="showAddBlockDialog" class="dialog-overlay">
        <div class="dialog-box">
          <h3>Neuen Block erstellen</h3>
          <input
            v-model="newBlockName"
            @keyup.enter="createBlock"
            type="text"
            placeholder="Blockname"
            class="block-input"
          />
          <div class="dialog-buttons">
            <button class="success-button" @click="createBlock">Erstellen</button>
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
            <button class="danger-button" @click="confirmDeleteBlock">Löschen</button>
            <button class="cancel-button" @click="closeDeleteBlockDialog">Abbrechen</button>
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
              <h3>{{ block.title }}</h3>

              <!-- Delete-Button (öffnet den Löschdialog) -->
              <div class="delete-button" @click="openDeleteBlockDialog(block)">✕</div>
            </div>
            <div :ref="el => setEditorRef(el, block.id)" class="editor"></div>
          </div>
        </template>
      </draggable>

      <!-- Debug-Ausgabe -->
      <div class="debug-info">
        <h4>Debug Information:</h4>
        <pre>{{ JSON.stringify(blocks, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { useRoute } from 'vue-router';
import * as Y from 'yjs';
import { QuillBinding } from 'y-quill';
import Quill from 'quill';
import QuillCursors from 'quill-cursors';
import { io } from 'socket.io-client';
import 'quill/dist/quill.snow.css';
import draggable from 'vuedraggable';
import printYDoc from "@/components/PromptEngineering/utils";
import sidebar from "@/components/PromptEngineering/sidebar.vue";

// QuillCursors-Registrierung
Quill.register('modules/cursors', QuillCursors);

const route = useRoute();
const promptId = computed(() => route.params.id || 1);
const roomId = computed(() => `room_${promptId.value}`);
const username = localStorage.getItem('username') || 'Unbekannter Benutzer';
const promptName = ref('');

// State Management
const blocks = ref([]);
const editorsMap = ref(new Map());
const editors = ref(new Map());
const bindings = ref(new Map());
const cursorsModules = ref(new Map());
const users = ref({});

const promptOwner = ref('');
const sharedWithUsers = ref([]);

let ydoc = null;
let socket = null;

// Fürs Hinzufügen neuer Blöcke
const showAddBlockDialog = ref(false);
const newBlockName = ref('');

// Snackbar
const showSnackbar = ref(false);
const snackbarMessage = ref('');

const showSnackbarMessage = (message) => {
  snackbarMessage.value = message;
  showSnackbar.value = true;

  // Setze die Sichtbarkeit nach der Animationsdauer auf false
  setTimeout(() => {
    showSnackbar.value = false;
  }, 3000); // Dauer muss mit der Gesamtdauer der Animation (CSS) übereinstimmen
};


// Für das Löschen von Blöcken
const showDeleteBlockDialog = ref(false);
const blockToDelete = ref(null);

/**
 * Dialog schließen und Eingabefeld (für neuen Block) zurücksetzen
 */
const closeAddBlockDialog = () => {
  showAddBlockDialog.value = false;
  newBlockName.value = '';
};

/**
 * Dialog für das Löschen schließen
 */
const closeDeleteBlockDialog = () => {
  showDeleteBlockDialog.value = false;
  blockToDelete.value = null;
};

/**
 * Methode zum Öffnen des Dialogs für das Löschen eines Blocks
 */
const openDeleteBlockDialog = (block) => {
  blockToDelete.value = block; // gemerkter Block, der gelöscht werden soll
  showDeleteBlockDialog.value = true;
};

/**
 * Bestätigte Löschung des Blocks
 */
const confirmDeleteBlock = () => {
  if (!blockToDelete.value || !ydoc) {
    closeDeleteBlockDialog();
    return;
  }

  const blockId = blockToDelete.value.id;

  // Y.Doc Update
  ydoc.transact(() => {
    const blocksMap = ydoc.getMap('blocks');
    if (blocksMap.has(blockId)) {
      blocksMap.delete(blockId);

      // Synchronisiere Update
      const update = Y.encodeStateAsUpdate(ydoc);
      if (socket?.connected) {
        socket.emit('sync_update', {
          room: roomId.value,
          update: Array.from(update)
        });
      }
    }
  });

  showSnackbarMessage(`Block "${blockToDelete.value.title}" wurde gelöscht!`);


  // Dialog schließen
  closeDeleteBlockDialog();
};

/**
 * Methode zum Erstellen eines neuen Blocks
 */
const createBlock = () => {
  const blockName = newBlockName.value.trim();
  if (!blockName) return;
  if (!ydoc) return;

  ydoc.transact(() => {
    const blocksMap = ydoc.getMap('blocks');

    // Prüfen, ob der Blockname schon existiert
    if (blocksMap.has(blockName)) {
      showSnackbarMessage(`Block "${blockName}" existiert bereits!`);

      return;
    }

    let maxPosition = 0;
    blocksMap.forEach((blockMap) => {
      const pos = blockMap.get('position');
      if (pos > maxPosition) {
        maxPosition = pos;
      }
    });

    // Neuen Block anlegen
    const newBlockMap = new Y.Map();
    newBlockMap.set('title', blockName);
    newBlockMap.set('position', maxPosition + 1);

    // Leerer Y.Text
    const ytext = new Y.Text();
    newBlockMap.set('content', ytext);

    // In blocksMap einfügen
    blocksMap.set(blockName, newBlockMap);

    // Explizit ein Update an den Server senden
    const update = Y.encodeStateAsUpdate(ydoc);
    if (socket?.connected) {
      socket.emit('sync_update', {
        room: roomId.value,
        update: Array.from(update)
      });
    }
  });

  // Debug-Ausgabe
  console.log("Neuer Block erstellt und synchronisiert");
  printYDoc(ydoc);

  showSnackbarMessage(`Block "${blockName}" wurde hinzugefügt!`);
  closeAddBlockDialog();
};

/**
 * Prompt Details laden
 */
const fetchPromptDetails = async () => {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await fetch(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${promptId.value}`,
      {
        headers: {
          'Authorization': api_key
        }
      }
    );
    const data = await response.json();

    if (response.ok) {
      promptName.value = data.name;
      // --- Hier neu:
      promptOwner.value = data.owner;
      sharedWithUsers.value = data.shared_with || [];
    } else {
      console.error('Fehler beim Abrufen der Prompt-Details:', data.error);
    }
  } catch (error) {
    console.error('Fehler beim Laden der Prompt-Details:', error);
  }
};

// Snackbar nach 3 Sek. ausblenden

/**
 * Watch und Lifecycle Hooks
 */
watch(
  () => blocks.value,
  async (newBlocks, oldBlocks) => {
    // Cleanup alte Editoren für gelöschte Blöcke
    if (oldBlocks) {
      const deletedBlocks = oldBlocks.filter(
        oldBlock => !newBlocks.find(newBlock => newBlock.id === oldBlock.id)
      );

      deletedBlocks.forEach(block => {
        const binding = bindings.value.get(block.id);
        if (binding) {
          binding.destroy();
          bindings.value.delete(block.id);
        }

        editors.value.delete(block.id);
        editorsMap.value.delete(block.id);
        cursorsModules.value.delete(block.id);
      });
    }

    // Initialisiere neue Editoren
    for (const block of newBlocks) {
      if (!editors.value.has(block.id)) {
        await nextTick(); // Warte auf DOM-Update
        await initializeEditor(block);
      }
    }
  },
  { deep: true }
);

/**
 * Sortierte Liste der Blocks
 */
const sortedBlocks = computed({
  get: () => {
    return [...blocks.value].sort((a, b) => a.position - b.position);
  },
  set: (newValue) => {
    // Update positions in blocks.value based on new order
    newValue.forEach((block, index) => {
      const originalBlock = blocks.value.find(b => b.id === block.id);
      if (originalBlock) {
        originalBlock.position = index;
      }
    });

    // Update positions in ydoc
    if (ydoc) {
      ydoc.transact(() => {
        const blocksMap = ydoc.getMap('blocks');
        newValue.forEach((block, index) => {
          const blockMap = blocksMap.get(block.id);
          if (blockMap) {
            blockMap.set('position', index);
          }
        });
      });

      // Sync changes with other clients
      const update = Y.encodeStateAsUpdate(ydoc);
      if (socket?.connected) {
        socket.emit('sync_update', {
          room: roomId.value,
          update: Array.from(update)
        });
      }
    }
  }
});

/**
 * Wird aufgerufen, wenn ein Drag beendet wurde
 */
const onDragEnd = () => {
  showSnackbarMessage(`Block-Reihenfolge aktualisiert!`);
};

/**
 * Alle Blocks in das lokale Array `blocks` laden
 */
const processYDoc = () => {
  const blocksMap = ydoc.getMap('blocks');
  const newBlocks = [];

  blocksMap.forEach((value, key) => {
    newBlocks.push({
      id: key,
      title: value.get('title'),
      position: value.get('position'),
      content: value.get('content')
    });
  });

  blocks.value = newBlocks;
};

/**
 * Debounce-Funktion für Cursor-Updates
 */
const debounce = (fn, delay) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
};

/**
 * Cursor-Positionen aktualisieren (z.B. wenn User tippt)
 */
const handleSelectionChange = (blockId) => {
  const debouncedEmit = debounce((range) => {
    if (socket?.connected) {
      socket.emit('cursor_update', {
        room: roomId.value,
        blockId,
        range: range
          ? {
              index: range.index,
              length: range.length
            }
          : null
      });
    }
  }, 50);

  return (range, oldRange, source) => {
    if (source === 'user') {
      if (!range) {
        // Entferne Cursor, wenn der Benutzer keinen Bereich mehr ausgewählt hat
        const cursorsModule = cursorsModules.value.get(blockId);
        if (cursorsModule) {
          cursorsModule.removeCursor(socket.id);
        }
      }
      debouncedEmit(range);
    }
  };
};

/**
 * Editor für einen Block initialisieren
 */
const initializeEditor = async (block) => {
  await nextTick();

  const editorElement = editorsMap.value.get(block.id);
  if (!editorElement || editors.value.has(block.id)) {
    return;
  }

  const blocksMap = ydoc.getMap('blocks');
  const blockMap = blocksMap.get(block.id);
  if (!blockMap) {
    console.error('Block map not found:', block.id);
    return;
  }

  let ytext = blockMap.get('content');
  if (!ytext) {
    ytext = new Y.Text();
    blockMap.set('content', ytext);

    // Wenn ein neuer ytext erstellt wurde, sofort synchronisieren
    const update = Y.encodeStateAsUpdate(ydoc);
    if (socket?.connected) {
      socket.emit('sync_update', {
        room: roomId.value,
        update: Array.from(update)
      });
    }
  }

  // Quill Editor mit angepassten Cursor-Einstellungen
  const editor = new Quill(editorElement, {
    modules: {
      cursors: {
        transformOnTextChange: true,
        hideDelayMs: 5000,
        hideSpeedMs: 500,
        selectionChangeSource: 'api'
      },
      toolbar: [
        ['bold', 'italic', 'underline'],
        ['clean']
      ],
      history: {
        userOnly: true
      }
    },
    theme: 'snow',
    placeholder: `Start editing ${block.title}...`
  });

  // Speichere Referenz zum Cursors Module
  const cursorsModule = editor.getModule('cursors');
  cursorsModules.value.set(block.id, cursorsModule);

  // Binding zwischen Yjs und Quill
  const binding = new QuillBinding(ytext, editor, null, {
    preserveCursor: true
  });

  // Selection-Change-Handler
  editor.on('selection-change', handleSelectionChange(block.id));

  // Text-Change-Handler
  editor.on('text-change', (delta, oldDelta, source) => {
    if (source === 'user') {
      ydoc.transact(() => {
        const blocksMap = ydoc.getMap('blocks');
        const blockMap = blocksMap.get(block.id);
        const ytext = blockMap.get('content');
        ytext.applyDelta(delta);

        const update = Y.encodeStateAsUpdate(ydoc);
        if (socket?.connected) {
          socket.emit('sync_update', {
            room: roomId.value,
            update: Array.from(update)
          });
        }
      });
    }
  });

  editors.value.set(block.id, editor);
  bindings.value.set(block.id, binding);
};

/**
 * Speichert die Editor-Referenz
 */
const setEditorRef = (el, blockId) => {
  if (el) {
    editorsMap.value.set(blockId, el);
  }
};

/**
 * Cursor aktualisieren (z.B. von anderen Usern)
 */
const updateCursor = (userId, cursor) => {
  // 1) Wenn cursor === null, entfernen wir den Cursor in allen Blöcken
  if (!cursor) {
    cursorsModules.value.forEach((cursorsModule) => {
      cursorsModule.removeCursor(userId);
    });
    return;
  }

  // 2) Wenn range === null, nur den Cursor in dem spezifischen Block entfernen
  const { blockId, range, username, color } = cursor;
  const cursorsModule = cursorsModules.value.get(blockId);
  const editor = editors.value.get(blockId);

  if (!range) {
    if (cursorsModule) {
      cursorsModule.removeCursor(userId);
    }
    return;
  }

  // 3) Falls es eine gültige Range gibt => Cursor aktualisieren
  if (cursorsModule && editor) {
    if (!cursorsModule.cursors().find(c => c.id === userId)) {
      cursorsModule.createCursor(userId, username, color);
    }

    const transformedRange = editor.getLength() < range.index
      ? { index: editor.getLength(), length: 0 }
      : range;

    cursorsModule.moveCursor(userId, transformedRange);
  }
};

/**
 * Socket Initialisierung
 */
const initializeSocket = () => {
  socket = io(import.meta.env.VITE_API_BASE_URL, {
    path: '/collab/socket.io/',
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000
  });

  socket.on('connect', () => {
    console.log('Connected to server');
    socket.emit('join_room', {
      room: roomId.value,
      username
    });
  });

  socket.on('snapshot_document', (fullUpdate) => {
    Y.applyUpdate(ydoc, new Uint8Array(fullUpdate));
    processYDoc();
  });

  socket.on('sync_update', ({ update }) => {
    Y.applyUpdate(ydoc, new Uint8Array(update));
    processYDoc();
  });

  socket.on('room_state', (state) => {
    users.value = state.users;
    nextTick(() => {
      Object.entries(state.cursors).forEach(([userId, cursor]) => {
        updateCursor(userId, cursor);
      });
    });
  });

  socket.on('user_joined', ({ userId, username, color }) => {
    users.value[userId] = { username, color };
  });

  socket.on('user_left', ({ userId }) => {
    delete users.value[userId];
    cursorsModules.value.forEach(cursorsModule => {
      cursorsModule.removeCursor(userId);
    });
  });

  socket.on('cursor_updated', ({ userId, cursor }) => {
    nextTick(() => updateCursor(userId, cursor));
  });

  socket.on('disconnect', () => {
    console.log('Disconnected from server');
  });
};

/**
 * Watch und Lifecycle Hooks
 */
watch(
  blocks,
  async (newBlocks) => {
    for (const block of newBlocks) {
      if (!editors.value.has(block.id)) {
        await initializeEditor(block);
      }
    }
  },
  { deep: true }
);

onMounted(async () => {
  await fetchPromptDetails();
  ydoc = new Y.Doc();
  initializeSocket();

  ydoc.on('update', (update) => {
    processYDoc();

    if (update.transaction?.local && socket?.connected) {
      const fullState = Y.encodeStateAsUpdate(ydoc);
      socket.emit('sync_update', {
        room: roomId.value,
        update: Array.from(fullState)
      });
    }
  });
});

onUnmounted(() => {
  bindings.value.forEach(binding => binding.destroy());
  editorsMap.value.clear();
  editors.value.clear();
  bindings.value.clear();
  cursorsModules.value.clear();
  socket?.disconnect();
  ydoc?.destroy();
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

/* Delete-Button im Block */
.delete-button {
  margin-left: auto;
  cursor: pointer;
  font-size: 1.2rem;
  color: #999;
  transition: color 0.2s;
}

.delete-button:hover {
  color: #e74c3c;
}
</style>
