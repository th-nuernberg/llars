import { ref, onMounted, onUnmounted } from 'vue'
import * as Y from 'yjs'
import { io } from 'socket.io-client'

export function useYjsCollaboration(roomId, username, onProcessYDoc, onUpdateCursor) {
  const ydoc = ref(null)
  const socket = ref(null)
  const users = ref({})

  const initializeSocket = () => {
    socket.value = io(import.meta.env.VITE_API_BASE_URL, {
      path: '/collab/socket.io/',
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000
    })

    socket.value.on('connect', () => {
      console.log('Connected to server')
      socket.value.emit('join_room', {
        room: roomId.value,
        username
      })
    })

    socket.value.on('snapshot_document', (fullUpdate) => {
      Y.applyUpdate(ydoc.value, new Uint8Array(fullUpdate))
      onProcessYDoc()
    })

    socket.value.on('sync_update', ({ update }) => {
      Y.applyUpdate(ydoc.value, new Uint8Array(update))
      onProcessYDoc()
    })

    socket.value.on('room_state', (state) => {
      users.value = state.users
      setTimeout(() => {
        Object.entries(state.cursors).forEach(([userId, cursor]) => {
          onUpdateCursor(userId, cursor)
        })
      }, 0)
    })

    socket.value.on('user_joined', ({ userId, username, color }) => {
      users.value[userId] = { username, color }
    })

    socket.value.on('user_left', ({ userId }) => {
      delete users.value[userId]
      // Cursor removal is handled by the calling component
    })

    socket.value.on('cursor_updated', ({ userId, cursor }) => {
      setTimeout(() => onUpdateCursor(userId, cursor), 0)
    })

    socket.value.on('disconnect', () => {
      console.log('Disconnected from server')
    })
  }

  const initialize = () => {
    ydoc.value = new Y.Doc()
    initializeSocket()

    ydoc.value.on('update', (update) => {
      onProcessYDoc()

      if (update.transaction?.local && socket.value?.connected) {
        const fullState = Y.encodeStateAsUpdate(ydoc.value)
        socket.value.emit('sync_update', {
          room: roomId.value,
          update: Array.from(fullState)
        })
      }
    })
  }

  const cleanup = () => {
    socket.value?.disconnect()
    ydoc.value?.destroy()
  }

  return {
    ydoc,
    socket,
    users,
    initialize,
    cleanup
  }
}
