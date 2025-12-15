import { ref, onMounted, onUnmounted } from 'vue'
import * as Y from 'yjs'
import { io } from 'socket.io-client'

export function useYjsCollaboration(roomId, username, onProcessYDoc, onUpdateCursor, options = {}) {
  const ydoc = ref(null)
  const socket = ref(null)
  const users = ref({})
  const { autoSync = false } = options || {}

  const getAuthToken = () => {
    if (typeof window === 'undefined') return null
    return sessionStorage.getItem('auth_token')
  }

  const clearAuthAndRedirectToLogin = () => {
    try {
      sessionStorage.removeItem('auth_token')
      sessionStorage.removeItem('auth_refreshToken')
      sessionStorage.removeItem('auth_idToken')
      sessionStorage.removeItem('auth_llars_roles')
      localStorage.removeItem('username')
    } catch {}

    if (typeof window !== 'undefined') {
      const current = `${window.location.pathname}${window.location.search}${window.location.hash}`
      window.location.href = `/login?redirect=${encodeURIComponent(current)}`
    }
  }

  const initializeSocket = () => {
    socket.value = io(import.meta.env.VITE_API_BASE_URL, {
      path: '/collab/socket.io/',
      auth: { token: getAuthToken() },
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

    socket.value.on('connect_error', (err) => {
      const msg = String(err?.message || err || '')
      console.error('Socket.IO connect_error:', msg)

      const lower = msg.toLowerCase()
      if (lower.includes('jwt expired') || lower.includes('authentication failed') || lower.includes('authentication required')) {
        try {
          socket.value?.disconnect()
        } catch {}
        clearAuthAndRedirectToLogin()
      }
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

    ydoc.value.on('update', (update, origin, doc, transaction) => {
      onProcessYDoc()

      if (autoSync && transaction?.local && socket.value?.connected) {
        socket.value.emit('sync_update', {
          room: roomId.value,
          update: Array.from(update)
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
