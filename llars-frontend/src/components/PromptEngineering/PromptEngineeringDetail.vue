<!-- PromptEnginnering.vue -->
<template>
  <div class="editor-container">
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

// Yjs document and socket
let ydoc = null;
let socket = null;

// Sortiere Blöcke nach Position
const sortedBlocks = computed(() => {
  return [...blocks.value].sort((a, b) => a.position - b.position);
});

// Verarbeite das YDoc und extrahiere die Blöcke
const processYDoc = () => {
  console.log('Processing YDoc...');
  const blocksMap = ydoc.getMap('blocks');
  const newBlocks = [];

  blocksMap.forEach((value, key) => {
    console.log('Processing block:', key);
    newBlocks.push({
      id: key,
      title: value.get('title'),
      position: value.get('position'),
      content: value.get('content')
    });
  });

  console.log('Processed blocks:', newBlocks);
  blocks.value = newBlocks;
};

// Initialisiere einen Editor für einen Block
const initializeEditor = async (block) => {
  console.log('Initializing editor for block:', block.id);

  await nextTick();

  const editorElement = editorsMap.value.get(block.id);
  if (!editorElement || editors.value.has(block.id)) {
    console.log('Editor already exists or element not found');
    return;
  }

  // Hole den YText für diesen Block
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

  console.log('Creating Quill editor...');
  const editor = new Quill(editorElement, {
    modules: {
      cursors: true,
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

  // Erstelle die Binding zwischen Yjs und Quill
  const binding = new QuillBinding(ytext, editor);

  // Text-Change Handler, um sicherzustellen, dass Änderungen erkannt werden
  editor.on('text-change', (delta, oldDelta, source) => {
    if (source === 'user') {
      // Führe die Änderung in einer Transaktion aus
      ydoc.transact(() => {
        // Hole das YText-Objekt für den aktuellen Block
        const blocksMap = ydoc.getMap('blocks');
        const blockMap = blocksMap.get(block.id);
        const ytext = blockMap.get('content');

        // Setze den gesamten Text neu (Beispielhaft)
        ytext.delete(0, ytext.length);
        ytext.insert(0, editor.getText());

        // Erstelle ein Update und schicke es an den Server
        const update = Y.encodeStateAsUpdate(ydoc);
        if (socket?.connected) {
          console.log('Sending sync_update to server...', {
            blockId: block.id,
            newContent: editor.getText(),
            updateSize: update.length
          });

          socket.emit('sync_update', {
            room: roomId.value,
            update: Array.from(update)
          });
        }
      });
    }
  });

  // Speichere Referenzen
  editors.value.set(block.id, editor);
  bindings.value.set(block.id, binding);

  console.log('Editor initialized:', {
    blockId: block.id,
    ytextContent: ytext.toString(),
    editorContent: editor.getText()
  });
};

// Speichere Editor-DOM-Referenzen
const setEditorRef = (el, blockId) => {
  if (el) {
    console.log('Setting editor ref for:', blockId);
    editorsMap.value.set(blockId, el);
  }
};

// Initialisiere Socket-Verbindung
const initializeSocket = () => {
  console.log('Initializing socket connection...');

  socket = io(import.meta.env.VITE_API_BASE_URL, {
    path: '/collab/socket.io/'
  });

  socket.on('connect', () => {
    console.log('Connected to server');
    socket.emit('join_room', {
      room: roomId.value,
      username
    });
  });

  // Event A: snapshot_document -> Erhalte den kompletten State vom Server
  socket.on('snapshot_document', (fullUpdate) => {
    console.log('Received snapshot_document');
    Y.applyUpdate(ydoc, new Uint8Array(fullUpdate));
    processYDoc();
  });

  // Event B: sync_update -> Erhalte ein Delta/Update von anderen Clients
  socket.on('sync_update', ({ update }) => {
    console.log('Received sync_update (delta)');
    Y.applyUpdate(ydoc, new Uint8Array(update));
    processYDoc();
  });

  socket.on('disconnect', () => {
    console.log('Disconnected from server');
  });
};

// Beobachte Änderungen an den Blöcken
watch(
  blocks,
  async (newBlocks) => {
    console.log('Blocks changed:', newBlocks);
    for (const block of newBlocks) {
      if (!editors.value.has(block.id)) {
        await initializeEditor(block);
      }
    }
  },
  { deep: true }
);

onMounted(async () => {
  console.log('Component mounted');

  // Initialisiere Yjs-Dokument
  ydoc = new Y.Doc();

  // Initialisiere Socket
  initializeSocket();

  // Wenn das YDoc lokale Änderungen erfährt, schicke inkrementelle Updates
  ydoc.on('update', (update, origin, doc) => {
    // Debug
    console.log('YDoc update detected:', {
      updateSize: update.length,
      origin,
      isLocal: update.transaction?.local
    });

    // Aktualisiere lokale Blocks
    processYDoc();

    // Nur bei lokalen Änderungen an den Server schicken (zweiter Sicherheitsmechanismus)
    if (update.transaction?.local && socket?.connected) {
      const fullState = Y.encodeStateAsUpdate(doc);
      socket.emit('sync_update', {
        room: roomId.value,
        update: Array.from(fullState)
      });
    }
  });
});

onUnmounted(() => {
  console.log('Component unmounting');
  // Cleanup
  bindings.value.forEach((binding) => binding.destroy());
  editorsMap.value.clear();
  editors.value.clear();
  bindings.value.clear();
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

.editor-block {
  margin-bottom: 30px;
}

.editor-block h3 {
  margin-bottom: 10px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
}

.editor {
  min-height: 150px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: #fff;
}

/* Debug Info */
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

/* Quill Styles */
:deep(.ql-container) {
  font-size: 16px;
}

:deep(.ql-editor) {
  min-height: 100px;
  padding: 15px;
}
</style>
