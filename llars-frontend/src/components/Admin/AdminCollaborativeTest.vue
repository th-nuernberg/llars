<template>
  <div class="collaborative-editor">
    <div v-for="(block, index) in blocks" :key="block.id" class="editor-block">
      <h3>{{ block.name }}</h3>
      <div :ref="el => editorsRef[index] = el" class="editor"></div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import * as Y from 'yjs'
import { QuillBinding } from 'y-quill'
import Quill from 'quill'
import QuillCursors from 'quill-cursors'
import { io } from 'socket.io-client'
import 'quill/dist/quill.snow.css'

Quill.register('modules/cursors', QuillCursors)

const blocks = ref([
  { id: 'block1', name: 'Block 1', content: '' },
  { id: 'block2', name: 'Block 2', content: '' }
])

const editorsRef = ref([])
const isConnected = ref(true)
const roomId = 'demo-room'

let ydoc = null
let editors = []
let bindings = []
let socket = null

const getUserInfo = () => {
  return {
    name: localStorage.getItem('username') || 'Anonymous',
    color: '#' + Math.floor(Math.random()*16777215).toString(16)
  }
}

const initializeSocketConnection = () => {
  socket = io(import.meta.env.VITE_API_BASE_URL)

  socket.on('connect', () => {
    console.log('Connected to server')
    socket.emit('join_room', roomId)

    socket.emit('set_user_info', {
      room: roomId,
      user: getUserInfo()
    })
  })

  socket.on('update_document', (update) => {
    const uint8Array = new Uint8Array(update)
    Y.applyUpdate(ydoc, uint8Array)
  })

  socket.on('cursor_update', (cursorInfo) => {
    if (editors[cursorInfo.blockId] && cursorInfo.userId !== socket.id) {
      const cursors = editors[cursorInfo.blockId].getModule('cursors')
      const existingCursor = cursors.cursors().find(cursor => cursor.id === cursorInfo.userId)

      if (!existingCursor) {
        cursors.createCursor(cursorInfo.userId, cursorInfo.name, cursorInfo.color)
      }

      if (cursorInfo.range) {
        cursors.moveCursor(cursorInfo.userId, cursorInfo.range)
        if (cursorInfo.range.length > 0) {
          cursors.toggleFlag(cursorInfo.userId, true)
        }
      } else {
        cursors.removeCursor(cursorInfo.userId)
      }
    }
  })

  socket.on('user_disconnected', (userId) => {
    editors.forEach(editor => {
      if (editor) {
        const cursors = editor.getModule('cursors')
        cursors.removeCursor(userId)
      }
    })
  })
}

const updateCursorPosition = (blockId, range) => {
  if (socket && editors[blockId]) {
    const userInfo = getUserInfo()
    socket.emit('cursor_update', {
      room: roomId,
      blockId: blockId,
      userId: socket.id,
      name: userInfo.name,
      color: userInfo.color,
      range: range
    })
  }
}

onMounted(() => {
  ydoc = new Y.Doc()
  initializeSocketConnection()

  // Initialize each editor
  blocks.value.forEach((block, index) => {
    const ytext = ydoc.getText(`block-${block.id}`)

    editors[block.id] = new Quill(editorsRef.value[index], {
      modules: {
        cursors: {
          transformOnTextChange: true,
          hideDelayMs: 2000,
          hideSpeedMs: 300,
          selectionChangeSource: 'api'
        },
        toolbar: [
          ['bold', 'italic', 'underline']
        ],
        history: {
          userOnly: true
        }
      },
      placeholder: `Start editing ${block.name}...`,
      theme: 'snow'
    })

    editors[block.id].root.style.fontSize = '18px'
    editors[block.id].root.style.lineHeight = '1.6'

    bindings[block.id] = new QuillBinding(ytext, editors[block.id])

    editors[block.id].on('selection-change', (range, oldRange, source) => {
      updateCursorPosition(block.id, range)
    })

    // Sync initial content
    ytext.observe(event => {
      block.content = editors[block.id].root.innerHTML
    })
  })

  ydoc.on('update', (update) => {
    socket.emit('document_update', {
      room: roomId,
      update: Array.from(update)
    })
  })
})

onUnmounted(() => {
  bindings.forEach(binding => binding && binding.destroy())
  if (ydoc) ydoc.destroy()
  if (socket) socket.disconnect()
})
</script>


<style scoped>
.collaborative-editor {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.editor-block {
  margin-bottom: 30px;
}

.editor-block h3 {
  margin-bottom: 10px;
}

.editor {
  min-height: 200px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

/* Cursor Module Styles */
:deep(.ql-container) {
  position: relative;
}

:deep(.ql-cursors) {
  position: absolute;
  left: 0;
  top: 0;
  pointer-events: none;
  z-index: 1;
}

:deep(.ql-cursor) {
  position: absolute;
  z-index: 2;
}

:deep(.ql-cursor-selections) {
  opacity: 0.5;
  pointer-events: none;
  z-index: 1;
}

:deep(.ql-cursor-caret-container) {
  position: absolute;
  margin-left: -1px;
  z-index: 2;
}

:deep(.ql-cursor-flag) {
  position: absolute;
  top: -16px;
  background: white;
  border-radius: 3px;
  padding: 2px 4px;
  font-size: 12px;
  white-space: nowrap;
  color: white;
  z-index: 3;
}

/* Editor Styles */
:deep(.ql-editor) {
  font-size: 18px !important;
  line-height: 1.6 !important;
  position: relative;
}

:deep(.ql-editor p) {
  margin-bottom: 1em;
}

/* Toolbar Styles */
:deep(.ql-toolbar.ql-snow) {
  position: relative;
  z-index: 4;
}

:deep(.ql-toolbar.ql-snow .ql-formats) {
  margin-right: 15px;
}

:deep(.ql-toolbar.ql-snow button) {
  width: 32px;
  height: 32px;
  padding: 6px;
}

:deep(.ql-toolbar.ql-snow button svg) {
  width: 20px;
  height: 20px;
}
</style>
