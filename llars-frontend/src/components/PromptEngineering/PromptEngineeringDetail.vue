<!-- PromptEngineering.vue -->
<template>
  <div class="layout-container">
    <sidebar
      :users="users"
      @showAddBlockDialog="showAddBlockDialog = true"
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
            <button @click="createBlock">Erstellen</button>
            <button @click="closeAddBlockDialog">Abbrechen</button>
          </div>
        </div>
      </div>

      <!-- Snackbar -->
      <div v-if="showSnackbar" class="snackbar">
        {{ snackbarMessage }}
      </div>

      <div v-for="block in sortedBlocks" :key="block.id" class="editor-block">
        <h3>{{ block.title }}</h3>
        <div :ref="el => setEditorRef(el, block.id)" class="editor"></div>
      </div>

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

let ydoc = null;
let socket = null;

// Fürs Hinzufügen neuer Blöcke
const showAddBlockDialog = ref(false);
const newBlockName = ref('');

// Snackbar
const showSnackbar = ref(false);
const snackbarMessage = ref('');

// Methode zum Schließen von Dialog und Löschen des Eingabefelds
const closeAddBlockDialog = () => {
  showAddBlockDialog.value = false;
  newBlockName.value = '';
};

// Methode zum Erstellen eines neuen Blocks
const createBlock = () => {
  const blockName = newBlockName.value.trim();
  if (!blockName) return;

  if (!ydoc) return;

  ydoc.transact(() => {
    const blocksMap = ydoc.getMap('blocks');

    if (blocksMap.has(blockName)) {
      showSnackbar.value = true;
      snackbarMessage.value = `Block "${blockName}" existiert bereits!`;
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

  snackbarMessage.value = `Block "${blockName}" wurde hinzugefügt!`;
  showSnackbar.value = true;
  closeAddBlockDialog();
};

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
    promptName.value = data.name;
  } catch (error) {
    console.error('Fehler beim Laden der Prompt-Details:', error);
  }
};
// Snackbar nach 3 Sek. ausblenden
watch(
  blocks,
  async (newBlocks) => {
    for (const block of newBlocks) {
      if (!editors.value.has(block.id)) {
        await initializeEditor(block);

        // Nach der Initialisierung eines neuen Blocks explizit den State synchronisieren
        const update = Y.encodeStateAsUpdate(ydoc);
        if (socket?.connected) {
          socket.emit('sync_update', {
            room: roomId.value,
            update: Array.from(update)
          });
        }
      }
    }
  },
  { deep: true }
);

// Debounce Funktion für Cursor Updates
const debounce = (fn, delay) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
};

// Sortiere Blöcke nach Position
const sortedBlocks = computed(() => {
  return [...blocks.value].sort((a, b) => a.position - b.position);
});

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

// Handler für Cursor-Bewegungen mit verbesserter Positionsberechnung
const handleSelectionChange = (blockId) => {
  const debouncedEmit = debounce((range) => {
    if (socket?.connected) {
      socket.emit('cursor_update', {
        room: roomId.value,
        blockId,
        range: range ? {
          index: range.index,
          length: range.length
        } : null
      });
    }
  }, 50);


  return (range, oldRange, source) => {
    if (source === 'user') {
      if (!range) {
        // Entferne Cursor, wenn der Benutzer keinen Bereich mehr ausgewählt hat
        const cursorsModule = cursorsModules.value.get(blockId);
        if (cursorsModule) {
          cursorsModule.removeCursor(socket.id); // Eigenen Cursor entfernen
        }
      }
      debouncedEmit(range);
    }
  };
};


// Initialisiere einen Editor für einen Block
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
        selectionChangeSource: 'api'  // Wichtig für korrekte Cursor-Synchronisation
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

  // Binding zwischen Yjs und Quill mit korrekter Cursor-Transformation
  const binding = new QuillBinding(ytext, editor, null, {
    preserveCursor: true  // Wichtig für korrekte Cursor-Position bei Updates
  });

  // Selection Change Handler für Cursor Updates
  editor.on('selection-change', handleSelectionChange(block.id));

  // Text Change Handler mit verbesserter Synchronisation
  editor.on('text-change', (delta, oldDelta, source) => {
    if (source === 'user') {
      ydoc.transact(() => {
        const blocksMap = ydoc.getMap('blocks');
        const blockMap = blocksMap.get(block.id);
        const ytext = blockMap.get('content');

        // Wende Delta direkt an statt Text neu zu setzen
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

const setEditorRef = (el, blockId) => {
  if (el) {
    editorsMap.value.set(blockId, el);
  }
};

// Verbesserte Cursor-Aktualisierung mit korrekter Positionsberechnung
const updateCursor = (userId, cursor) => {
  // 1) Wenn cursor === null, entfernen wir den Cursor in allen Blöcken
  if (!cursor) {
    // Dieser Nutzer hat gar keinen Cursor mehr
    cursorsModules.value.forEach((cursorsModule) => {
      cursorsModule.removeCursor(userId);
    });
    return; // direkt abbrechen
  }

  // 2) Wenn range === null, nur den Cursor in dem spezifischen Block entfernen
  const { blockId, range, username, color } = cursor;
  const cursorsModule = cursorsModules.value.get(blockId);
  const editor = editors.value.get(blockId);

  if (!range) {
    // Null-Range => Cursor entfernen
    if (cursorsModule) {
      cursorsModule.removeCursor(userId);
    }
    return; // abbrechen
  }

  // 3) Falls es eine gültige Range gibt => Cursor aktualisieren
  if (cursorsModule && editor) {
    // Cursor ggf. neu anlegen
    if (!cursorsModule.cursors().find(c => c.id === userId)) {
      cursorsModule.createCursor(userId, username, color);
    }

    // Range transformieren (falls index zu groß ist)
    const transformedRange = editor.getLength() < range.index
      ? { index: editor.getLength(), length: 0 }
      : range;

    cursorsModule.moveCursor(userId, transformedRange);
  }
};


// Socket Initialisierung mit verbessertem Cursor-Handling
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
    // Aktualisiere alle Cursors mit Verzögerung
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
      cursorsModule.removeCursor(userId); // Entferne Cursor des Benutzers
    });
  });


  socket.on('cursor_updated', ({ userId, cursor }) => {
    nextTick(() => updateCursor(userId, cursor));
  });

  socket.on('disconnect', () => {
    console.log('Disconnected from server');
  });
};

// Watch und Lifecycle Hooks
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
  padding: 20px;
  border-radius: 6px;
  min-width: 300px;
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

.snackbar {
  position: fixed;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  background: #323232;
  color: white;
  padding: 10px 20px;
  border-radius: 4px;
  animation: fadein 0.5s;
  z-index: 999;
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

</style>
