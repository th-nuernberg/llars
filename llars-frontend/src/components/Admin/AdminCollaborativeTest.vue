<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import * as Y from 'yjs'
import { WebrtcProvider } from 'y-webrtc'
import { QuillBinding } from 'y-quill'
import Quill from 'quill'
import QuillCursors from 'quill-cursors'
import 'quill/dist/quill.snow.css'

Quill.register('modules/cursors', QuillCursors)

const editorRef = ref(null)
let ydoc = null
let provider = null
let editor = null
let binding = null

const isConnected = ref(true)

const toggleConnection = () => {
  if (provider) {
    if (provider.shouldConnect) {
      provider.disconnect()
      isConnected.value = false
    } else {
      provider.connect()
      isConnected.value = true
    }
  }
}

onMounted(() => {
  // Initialize Yjs document
  ydoc = new Y.Doc()

  // Initialize WebRTC provider
  provider = new WebrtcProvider('quill-demo-room', ydoc)

  // Get shared text type
  const ytext = ydoc.getText('quill')

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
  binding = new QuillBinding(ytext, editor, provider.awareness)

  // Optional: Set user information
  provider.awareness.setLocalStateField('user', {
    name: 'User ' + Math.floor(Math.random() * 100),
    color: '#' + Math.floor(Math.random()*16777215).toString(16)
  })
})

onUnmounted(() => {
  // Clean up
  if (binding) binding.destroy()
  if (provider) provider.destroy()
  if (ydoc) ydoc.destroy()
})
</script>

<template>
  <div class="collaborative-editor">
    <button @click="toggleConnection">
      {{ isConnected ? 'Disconnect' : 'Connect' }}
    </button>

    <div class="editor-info">
      <p>This is a collaborative editor using Yjs and Quill</p>
      <p>The content of this editor is shared with every client in the same room</p>
    </div>

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

.editor-info {
  margin: 20px 0;
}

.editor {
  min-height: 500px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
</style>
