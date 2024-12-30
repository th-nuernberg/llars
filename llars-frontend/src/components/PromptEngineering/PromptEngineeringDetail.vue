<template>
  <div class="editor-container">
    <!-- Editor blocks will be rendered in order based on their position -->
    <div v-for="block in sortedBlocks" :key="block.id" class="editor-block">
      <h3>{{ block.title }}</h3>
      <!-- Each editor needs a unique container -->
      <div :ref="el => setEditorRef(el, block.id)" class="editor"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import * as Y from 'yjs';
import { QuillBinding } from 'y-quill';
import Quill from 'quill';
import QuillCursors from 'quill-cursors';
import { io } from 'socket.io-client';
import 'quill/dist/quill.snow.css';
import printYDoc from "@/components/PromptEngineering/utils";

// Register the cursors module with Quill
Quill.register('modules/cursors', QuillCursors);

const route = useRoute();
const promptId = computed(() => route.params.id || 1);
const roomId = computed(() => `room_${promptId.value}`);
const username = localStorage.getItem('username') || 'Unbekannter Benutzer';

// State management
const blocks = ref([]);
const editorsMap = ref(new Map()); // Stores references to editor DOM elements
const editors = ref(new Map()); // Stores Quill instances
const bindings = ref(new Map()); // Stores Y-Quill bindings

// Reference to our Yjs document and socket connection
let ydoc = null;
let socket = null;

// Sort blocks by position
const sortedBlocks = computed(() => {
  return [...blocks.value].sort((a, b) => a.position - b.position);
});

// Store editor DOM element references
const setEditorRef = (el, blockId) => {
  if (el) {
    editorsMap.value.set(blockId, el);
  }
};

// Initialize a Quill editor for a block
const initializeEditor = (block) => {
  const editorElement = editorsMap.value.get(block.id);
  if (!editorElement || editors.value.has(block.id)) return;

  // Get the YText instance for this block
  const ytext = ydoc.getText(`block-${block.id}`);

  // Create Quill editor
  const editor = new Quill(editorElement, {
    modules: {
      cursors: {
        transformOnTextChange: true,
        hideDelayMs: 2000,
        hideSpeedMs: 300,
      },
      toolbar: [
        ['bold', 'italic', 'underline'],
        ['clean']
      ],
    },
    theme: 'snow',
    placeholder: `Start editing ${block.title}...`,
  });

  // Create binding between Yjs and Quill
  const binding = new QuillBinding(ytext, editor);

  // Store references
  editors.value.set(block.id, editor);
  bindings.value.set(block.id, binding);

  // Handle cursor updates
  editor.on('selection-change', (range) => {
    if (range && socket) {
      socket.emit('cursor_update', {
        room: roomId.value,
        blockId: block.id,
        range,
        username
      });
    }
  });
};

// Process the YDoc structure into our blocks array
const processYDoc = () => {
  const blocksMap = ydoc.getMap('blocks');
  const processedBlocks = [];

  blocksMap.forEach((value, key) => {
    processedBlocks.push({
      id: key,
      title: value.get('title'),
      position: value.get('position'),
      content: value.get('content')
    });
  });

  blocks.value = processedBlocks;
};

// Initialize socket connection
const initializeSocket = () => {
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

  socket.on('update_document', (update) => {
    Y.applyUpdate(ydoc, new Uint8Array(update));
    printYDoc(ydoc);

  });

  socket.on('cursor_updated', ({ userId, blockId, range, username: remoteUsername }) => {
    const editor = editors.value.get(blockId);
    if (editor && userId !== socket.id) {
      const cursors = editor.getModule('cursors');
      if (range) {
        cursors.createCursor(userId, remoteUsername, getRandomColor());
        cursors.moveCursor(userId, range);
      } else {
        cursors.removeCursor(userId);
      }
    }
  });

  socket.on('disconnect', () => {
    console.log('Disconnected from server');
  });
};

// Helper function to generate random colors for cursors
const getRandomColor = () => {
  return `#${Math.floor(Math.random()*16777215).toString(16)}`;
};

// Lifecycle hooks
onMounted(() => {
  // Initialize Yjs document
  ydoc = new Y.Doc();

  // Initialize socket connection
  initializeSocket();

  // Set up Yjs update handling
  ydoc.on('update', (update) => {
    processYDoc();
    if (socket && socket.connected) {
      socket.emit('document_update', {
        room: roomId.value,
        update: Array.from(update)
      });
    }
  });

  // Watch for changes in blocks and initialize editors
  blocks.value.forEach(initializeEditor);
});

onUnmounted(() => {
  // Clean up
  bindings.value.forEach(binding => binding.destroy());
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

/* Quill editor styles */
:deep(.ql-toolbar) {
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
}

:deep(.ql-container) {
  border-bottom-left-radius: 4px;
  border-bottom-right-radius: 4px;
}

:deep(.ql-editor) {
  min-height: 100px;
  font-size: 16px;
  line-height: 1.6;
}
</style>
