<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import * as Y from 'yjs'
import { QuillBinding } from 'y-quill'
import Quill from 'quill'
import QuillCursors from 'quill-cursors'
import { io } from 'socket.io-client'
import 'quill/dist/quill.snow.css'

Quill.register('modules/cursors', QuillCursors)

const editorRef = ref(null)
let ydoc = null
let editor = null
let binding = null
let socket = null
const roomId = 'demo-room'
const isConnected = ref(true)

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
    if (editor && cursorInfo.userId !== socket.id) {
      const cursors = editor.getModule('cursors')
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
    if (editor) {
      const cursors = editor.getModule('cursors')
      cursors.removeCursor(userId)
    }
  })
}

const updateCursorPosition = (range) => {
  if (socket && editor) {
    const userInfo = getUserInfo()
    socket.emit('cursor_update', {
      room: roomId,
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
  const ytext = ydoc.getText('quill')

  ydoc.on('update', (update) => {
    socket.emit('document_update', {
      room: roomId,
      update: Array.from(update)
    })
  })

  editor = new Quill(editorRef.value, {
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
    placeholder: 'Start collaborating...',
    theme: 'snow'
  })

  editor.root.style.fontSize = '18px'
  editor.root.style.lineHeight = '1.6'

  binding = new QuillBinding(ytext, editor)

  editor.on('selection-change', (range, oldRange, source) => {
    updateCursorPosition(range)
  })
})

onUnmounted(() => {
  if (binding) binding.destroy()
  if (ydoc) ydoc.destroy()
  if (socket) socket.disconnect()
})
</script>

<template>
  <div class="collaborative-editor">
    <div ref="editorRef" class="editor"></div>
  </div>
</template>

<style scoped>
.collaborative-editor {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  position: relative;
}

.editor {
  min-height: 500px;
  border: 1px solid #ccc;
  border-radius: 4px;
  position: relative;
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
