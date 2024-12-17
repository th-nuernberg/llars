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
    color: '#' + Math.floor(Math.random()*16777215).toString(16) // Zufällige Farbe
  }
}

const initializeSocketConnection = () => {
  socket = io(import.meta.env.VITE_API_BASE_URL)

  socket.on('connect', () => {
    console.log('Connected to server')
    socket.emit('join_room', roomId)

    // Sende initiale Benutzerinformation
    socket.emit('set_user_info', {
      room: roomId,
      user: getUserInfo()
    })
  })

  socket.on('update_document', (update) => {
    const uint8Array = new Uint8Array(update)
    Y.applyUpdate(ydoc, uint8Array)
  })

  // Empfange Cursor-Updates
  socket.on('cursor_update', (cursorInfo) => {
    if (editor && cursorInfo.userId !== socket.id) {
      const cursors = editor.getModule('cursors')
      cursors.createCursor(cursorInfo.userId, cursorInfo.name, cursorInfo.color)
      cursors.moveCursor(cursorInfo.userId, cursorInfo.range)
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
  // Initialize Yjs document
  ydoc = new Y.Doc()

  // Initialize Socket.IO connection
  initializeSocketConnection()

  // Get shared text type
  const ytext = ydoc.getText('quill')

  // Listen for document updates
  ydoc.on('update', (update) => {
    socket.emit('document_update', {
      room: roomId,
      update: Array.from(update)
    })
  })

  // Initialize Quill editor
  editor = new Quill(editorRef.value, {
    modules: {
      cursors: true,
      toolbar: [
        [{ header: [1, 2, false] }],
        ['bold', 'italic', 'underline'],
        ['image', 'code-block']
      ],
      history: {
        userOnly: true
      }
    },
    placeholder: 'Start collaborating...',
    theme: 'snow'
  })

  // Bind Quill to Yjs
  binding = new QuillBinding(ytext, editor)

  // Cursor-Position-Tracking
  editor.on('selection-change', (range) => {
    if (range) {
      updateCursorPosition(range)
    }
  })
})

onUnmounted(() => {
  // Clean up
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
}

.editor {
  min-height: 500px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
</style>
