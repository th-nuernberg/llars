<!-- PromptEngineering.vue -->
<template>
  <div class="editor-container">
    <div class="users-list">
      <h3>Online Users:</h3>
      <div v-for="(user, id) in users" :key="id" class="user-item">
        <span class="user-dot" :style="{ backgroundColor: user.color }"></span>
        {{ user.username }}
      </div>
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

// Register QuillCursors
Quill.register('modules/cursors', QuillCursors);

const route = useRoute();
const promptId = computed(() => route.params.id || 1);
const roomId = computed(() => `room_${promptId.value}`);
const username = localStorage.getItem('username') || 'Unbekannter Benutzer';

// State Management
const blocks = ref([]);
const editorsMap = ref(new Map());
const editors = ref(new Map());
const bindings = ref(new Map());
const cursorsModules = ref(new Map());
const users = ref({});

// Yjs document and socket
let ydoc = null;
let socket = null;

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
  }, 50); // 50ms Debounce

  return (range, oldRange, source) => {
    if (source === 'user') {
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
  const { blockId, range, username, color } = cursor;
  const cursorsModule = cursorsModules.value.get(blockId);
  const editor = editors.value.get(blockId);

  if (cursorsModule && editor && range) {
    // Stelle sicher, dass der Cursor existiert
    if (!cursorsModule.cursors().find(c => c.id === userId)) {
      cursorsModule.createCursor(userId, username, color);
    }

    // Aktualisiere die Position mit korrekter Range-Transformation
    const transformedRange = editor.getLength() < range.index ?
      { index: editor.getLength(), length: 0 } : range;

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
</style>
