import { ref, onMounted, onUnmounted } from 'vue'
import * as Y from 'yjs'
import { io } from 'socket.io-client'
import { AUTH_STORAGE_KEYS, clearAuthStorage, getAuthStorageItem } from '@/utils/authStorage'

export function useYjsCollaboration(roomId, username, onProcessYDoc, onUpdateCursor, options = {}) {
  const ydoc = ref(null)
  const socket = ref(null)
  const users = ref({})
  const { autoSync = false } = options || {}
  const socketioEnableWebsocket = String(import.meta.env.VITE_SOCKETIO_ENABLE_WEBSOCKET || '').toLowerCase() === 'true'
  const socketioTransports = socketioEnableWebsocket ? ['polling', 'websocket'] : ['polling']

  // Flag to prevent echo when applying remote updates
  let applyingRemoteUpdate = false

  const getAuthToken = () => {
    if (typeof window === 'undefined') return null
    return getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  }

  const getSocketBaseUrl = () => {
    if (typeof window === 'undefined') {
      return import.meta.env.VITE_API_BASE_URL || ''
    }
    const rawBase = import.meta.env.VITE_API_BASE_URL || window.location.origin
    const trimmed = String(rawBase || '').replace(/\/+$/, '')
    if (trimmed.endsWith('/api')) {
      return trimmed.slice(0, -4)
    }
    return trimmed || window.location.origin
  }

  const getCollabColor = () => {
    if (typeof window === 'undefined') return null
    return getAuthStorageItem(AUTH_STORAGE_KEYS.collabColor) || null
  }

  const clearAuthAndRedirectToLogin = () => {
    clearAuthStorage()
    try {
      localStorage.removeItem('username')
    } catch {}

    if (typeof window !== 'undefined') {
      const current = `${window.location.pathname}${window.location.search}${window.location.hash}`
      window.location.href = `/login?redirect=${encodeURIComponent(current)}`
    }
  }

  const initializeSocket = () => {
    socket.value = io(getSocketBaseUrl(), {
      path: '/collab/socket.io/',
      auth: {
        token: getAuthToken(),
        color: getCollabColor()  // Send persisted collab color
      },
      transports: socketioTransports,
      upgrade: socketioEnableWebsocket,
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
      applyingRemoteUpdate = true
      try {
        Y.applyUpdate(ydoc.value, new Uint8Array(fullUpdate))
      } finally {
        applyingRemoteUpdate = false
      }
      onProcessYDoc()
    })

    socket.value.on('sync_update', ({ update }) => {
      applyingRemoteUpdate = true
      try {
        Y.applyUpdate(ydoc.value, new Uint8Array(update))
      } finally {
        applyingRemoteUpdate = false
      }
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

    // Handle color updates from other users
    socket.value.on('user_color_updated', ({ userId, username, color }) => {
      if (users.value[userId]) {
        users.value[userId] = { ...users.value[userId], color }
      }
      // Trigger callback if provided (for UI updates)
      if (options.onColorUpdate) {
        options.onColorUpdate(userId, color)
      }
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

      // Only send updates that are truly local (not from remote sync)
      // The applyingRemoteUpdate flag prevents echo from QuillBinding
      // reacting to remote Yjs changes and creating new local updates
      if (autoSync && transaction?.local && !applyingRemoteUpdate && socket.value?.connected) {
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

  /**
   * Broadcast color update to all users in the current room
   * Call this after saving a new color to the database
   */
  const updateColor = (newColor) => {
    if (!newColor || !roomId.value) return

    if (users.value) {
      const next = { ...users.value }
      let updated = false
      for (const [userId, user] of Object.entries(next)) {
        if (user?.username === username) {
          next[userId] = { ...user, color: newColor }
          updated = true
        }
      }
      if (updated) {
        users.value = next
      }
    }

    if (!socket.value?.connected) return

    socket.value.emit('update_color', {
      room: roomId.value,
      color: newColor
    })
  }

  /**
   * Switch to a different room (document) without recreating the socket connection
   * This allows fast document switching without full reconnection
   */
  const switchRoom = (oldRoom, newRoom) => {
    if (!socket.value?.connected || !newRoom) return

    // Leave old room
    if (oldRoom) {
      socket.value.emit('leave_room', { room: oldRoom })
    }

    // Clear users from old room
    users.value = {}

    // Create fresh Yjs doc for new room
    if (ydoc.value) {
      ydoc.value.destroy()
    }
    ydoc.value = new Y.Doc()

    // Set up update handler for new doc
    ydoc.value.on('update', (update, origin, doc, transaction) => {
      onProcessYDoc()

      if (autoSync && transaction?.local && !applyingRemoteUpdate && socket.value?.connected) {
        socket.value.emit('sync_update', {
          room: roomId.value,
          update: Array.from(update)
        })
      }
    })

    // Join new room
    socket.value.emit('join_room', {
      room: newRoom,
      username
    })
  }

  return {
    ydoc,
    socket,
    users,
    initialize,
    cleanup,
    updateColor,
    switchRoom
  }
}
