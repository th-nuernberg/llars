/**
 * @fileoverview Vue composable for Yjs-based real-time collaborative editing.
 *
 * This composable provides the client-side integration with the LLARS collaborative
 * editing system. It handles:
 * - Socket.IO connection to the YJS WebSocket server
 * - Yjs document synchronization via CRDTs
 * - Multi-user cursor tracking
 * - Real-time Git panel update notifications via `document_saved` events
 *
 * @module useYjsCollaboration
 * @requires yjs
 * @requires socket.io-client
 */

import { ref, onMounted, onUnmounted } from 'vue'
import * as Y from 'yjs'
import { io } from 'socket.io-client'
import { AUTH_STORAGE_KEYS, clearAuthStorage, getAuthStorageItem } from '@/utils/authStorage'

/**
 * Calculate character-level diff between two strings.
 * Uses common prefix/suffix detection for efficient O(n) calculation.
 *
 * @param {string} baseline - The original/committed content
 * @param {string} current - The current content
 * @returns {{insertions: number, deletions: number, hasChanges: boolean}} Character counts
 */
function calculateCharDiff(baseline, current) {
  if (baseline === current) {
    return { insertions: 0, deletions: 0, hasChanges: false }
  }

  const baseLen = baseline.length
  const currLen = current.length

  // For very long strings, use a simpler heuristic
  if (baseLen > 50000 || currLen > 50000) {
    const lenDiff = currLen - baseLen
    return {
      insertions: Math.max(0, lenDiff),
      deletions: Math.max(0, -lenDiff),
      hasChanges: true
    }
  }

  // Find common prefix
  let prefixLen = 0
  const minLen = Math.min(baseLen, currLen)
  while (prefixLen < minLen && baseline[prefixLen] === current[prefixLen]) {
    prefixLen++
  }

  // Find common suffix (but don't overlap with prefix)
  let suffixLen = 0
  while (
    suffixLen < minLen - prefixLen &&
    baseline[baseLen - 1 - suffixLen] === current[currLen - 1 - suffixLen]
  ) {
    suffixLen++
  }

  // The middle part is what changed
  const baseMiddle = baseLen - prefixLen - suffixLen
  const currMiddle = currLen - prefixLen - suffixLen

  return {
    insertions: Math.max(0, currMiddle),
    deletions: Math.max(0, baseMiddle),
    hasChanges: true
  }
}

/**
 * Vue composable for Yjs-based real-time collaboration.
 *
 * Establishes a Socket.IO connection to the YJS server and manages
 * bidirectional synchronization of Yjs documents.
 *
 * @param {import('vue').Ref<string>} roomId - Reactive room ID (e.g., 'latex_42')
 * @param {string} username - Current user's username for presence display
 * @param {Function} onProcessYDoc - Callback invoked after Yjs updates (to refresh editor)
 * @param {Function} onUpdateCursor - Callback for cursor position updates `(userId, cursor) => void`
 * @param {Object} [options={}] - Additional options
 * @param {boolean} [options.autoSync=false] - Automatically sync local changes to server
 * @param {Function} [options.onColorUpdate] - Callback when user color changes `(userId, color) => void`
 * @param {Function} [options.onDocumentSaved] - Callback for document_saved events (Git panel refresh after 2s debounce)
 * @param {Function} [options.onDocumentUpdated] - Callback for document_updated events (instant Git panel refresh on every keystroke)
 * @param {Function} [options.onDiffCalculated] - Callback for local diff calculation `({insertions, deletions, hasChanges}) => void`
 *
 * @returns {Object} Composable API
 * @returns {import('vue').Ref<Y.Doc>} returns.ydoc - Reactive Yjs document
 * @returns {import('vue').Ref<Socket>} returns.socket - Socket.IO connection
 * @returns {import('vue').Ref<Object>} returns.users - Connected users by socket ID
 * @returns {Function} returns.initialize - Initialize connection
 * @returns {Function} returns.cleanup - Cleanup connection
 * @returns {Function} returns.updateColor - Broadcast color change
 * @returns {Function} returns.switchRoom - Switch to different document
 * @returns {Function} returns.reloadRoom - Reload current room from DB
 * @returns {Function} returns.reloadAnyRoom - Reload any room from DB
 *
 * @example
 * // Basic usage in a Vue component
 * const { ydoc, users, initialize, cleanup } = useYjsCollaboration(
 *   roomId,
 *   username,
 *   () => updateEditorContent(),
 *   (userId, cursor) => updateCursorDisplay(userId, cursor),
 *   {
 *     autoSync: true,
 *     onDocumentSaved: (data) => {
 *       // Refresh Git panel when any document in workspace is saved
 *       gitPanelRef.value?.checkForChanges?.()
 *     }
 *   }
 * )
 *
 * onMounted(() => initialize())
 * onUnmounted(() => cleanup())
 */
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
      console.log('[useYjsCollaboration] Connected to YJS server, joining room:', roomId.value)
      socket.value.emit('join_room', {
        room: roomId.value,
        username
      })
    })

    // Debug: Log ALL incoming events
    socket.value.onAny((eventName, ...args) => {
      console.log(`[useYjsCollaboration] Event received: ${eventName}`, args)
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

    // =====================================================================
    // Real-time Git Panel Update: Listen for document_saved events
    // =====================================================================
    // The YJS server broadcasts this event to all clients in the workspace
    // room whenever any document is persisted to the database (after the
    // 2-second debounce). This enables the Git panel to refresh and show
    // uncommitted changes in real-time.
    //
    // Event payload: { documentId, workspaceId, kind, contentLength, savedAt }
    //
    // The parent component should pass an onDocumentSaved callback that
    // triggers gitPanelRef.value?.checkForChanges?.() to refresh the panel.
    // =====================================================================
    socket.value.on('document_saved', (data) => {
      console.log('[useYjsCollaboration] document_saved received:', data)
      if (options.onDocumentSaved) {
        options.onDocumentSaved(data)
      }
    })

    // =====================================================================
    // Real-time Git Panel Update: Listen for document_updated events
    // =====================================================================
    // Unlike document_saved (which fires after 2s debounce), this event
    // fires on EVERY sync_update, enabling instant Git panel updates.
    // All users in the workspace see changes immediately as they're typed.
    //
    // Event payload: { documentId, workspaceId, kind, timestamp }
    //
    // The parent component should pass an onDocumentUpdated callback that
    // triggers gitPanelRef.value?.checkForChanges?.() to refresh the panel.
    // =====================================================================
    socket.value.on('document_updated', (data) => {
      if (options.onDocumentUpdated) {
        options.onDocumentUpdated(data)
      }
    })

    // =====================================================================
    // Force Reload: Handle document revert/rollback from other users
    // =====================================================================
    // When another user reverts a document, the server sends force_reload
    // to ALL clients in the room. Unlike snapshot_document (which merges),
    // force_reload requires clients to completely recreate their ydoc.
    //
    // Without this, content would be duplicated because Y.applyUpdate()
    // merges CRDT states instead of replacing them.
    // =====================================================================
    socket.value.on('force_reload', (data) => {
      console.log('[useYjsCollaboration] force_reload received:', data.room)

      // Only process if this is our current room
      if (data.room !== roomId.value) {
        console.log('[useYjsCollaboration] force_reload ignored - different room')
        return
      }

      console.log('[useYjsCollaboration] force_reload - recreating ydoc for room:', data.room)

      // Destroy existing ydoc to clear all local state
      if (ydoc.value) {
        ydoc.value.destroy()
      }

      // Create fresh ydoc
      ydoc.value = new Y.Doc()

      // Apply the snapshot from server
      applyingRemoteUpdate = true
      try {
        Y.applyUpdate(ydoc.value, new Uint8Array(data.snapshot))
      } finally {
        applyingRemoteUpdate = false
      }

      // Re-setup update handler for the new doc
      ydoc.value.on('update', (update, origin, doc, transaction) => {
        onProcessYDoc()

        // Calculate diff for instant Git panel updates
        emitDiffIfNeeded()

        if (autoSync && transaction?.local && !applyingRemoteUpdate && socket.value?.connected) {
          socket.value.emit('sync_update', {
            room: roomId.value,
            update: Array.from(update)
          })
        }
      })

      // Refresh the editor with new content
      onProcessYDoc()

      console.log('[useYjsCollaboration] force_reload complete')
    })

    socket.value.on('disconnect', () => {
      console.log('Disconnected from server')
    })
  }

  /**
   * Calculate and emit diff against baseline.
   * Called on every YJS update for instant Git panel updates.
   */
  const emitDiffIfNeeded = () => {
    if (!options.onDiffCalculated || !ydoc.value) return

    try {
      const baselineMap = ydoc.value.getMap('baseline')
      const baseline = baselineMap.get('text') || ''
      const current = ydoc.value.getText('content').toString()
      const diff = calculateCharDiff(baseline, current)
      options.onDiffCalculated(diff)
    } catch (e) {
      // Ignore errors during initial setup
    }
  }

  const initialize = () => {
    ydoc.value = new Y.Doc()
    initializeSocket()

    ydoc.value.on('update', (update, origin, doc, transaction) => {
      onProcessYDoc()

      // Calculate diff for instant Git panel updates
      emitDiffIfNeeded()

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

      // Calculate diff for instant Git panel updates
      emitDiffIfNeeded()

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

  /**
   * Reload the current room from the database.
   * Used after rollback/revert operations to sync editor with DB state.
   * The server will broadcast the new snapshot to all connected clients.
   */
  const reloadRoom = () => {
    return new Promise((resolve) => {
      console.log('[reloadRoom] Called, socket connected:', socket.value?.connected, 'roomId:', roomId.value)
      if (!socket.value?.connected || !roomId.value) {
        console.warn('[reloadRoom] Aborting - socket not connected or no roomId')
        resolve(false)
        return
      }

      const room = roomId.value
      console.log('[reloadRoom] Emitting reload_room for room:', room)

      // Create a fresh Yjs doc to receive the reloaded content
      if (ydoc.value) {
        ydoc.value.destroy()
      }
      ydoc.value = new Y.Doc()

      // Set up update handler for the new doc
      ydoc.value.on('update', (update, origin, doc, transaction) => {
        onProcessYDoc()

        // Calculate diff for instant Git panel updates
        emitDiffIfNeeded()

        if (autoSync && transaction?.local && !applyingRemoteUpdate && socket.value?.connected) {
          socket.value.emit('sync_update', {
            room: roomId.value,
            update: Array.from(update)
          })
        }
      })

      let finished = false
      const timeout = setTimeout(() => {
        if (finished) return
        finished = true
        resolve(false)
      }, 5000)

      socket.value.emit('reload_room', { room }, (response) => {
        if (finished) return
        clearTimeout(timeout)
        finished = true
        resolve(!!response?.success)
      })
    })
  }

  /**
   * Reload any room from the database (not just the current room).
   * Used to invalidate YJS cache when reverting a document that is not currently open.
   * This only sends the reload event to the server - no local ydoc changes.
   */
  const reloadAnyRoom = (roomName) => {
    return new Promise((resolve) => {
      console.log('[reloadAnyRoom] Called for room:', roomName, 'socket connected:', socket.value?.connected)
      if (!socket.value?.connected || !roomName) {
        console.warn('[reloadAnyRoom] Aborting - socket not connected or no roomName')
        resolve(false)
        return
      }

      console.log('[reloadAnyRoom] Emitting reload_room for room:', roomName)

      let finished = false
      const timeout = setTimeout(() => {
        if (finished) return
        finished = true
        console.warn('[reloadAnyRoom] Timeout waiting for response')
        resolve(false)
      }, 5000)

      socket.value.emit('reload_room', { room: roomName }, (response) => {
        if (finished) return
        clearTimeout(timeout)
        finished = true
        console.log('[reloadAnyRoom] Server response:', response)
        resolve(!!response?.success)
      })
    })
  }

  return {
    ydoc,
    socket,
    users,
    initialize,
    cleanup,
    updateColor,
    switchRoom,
    reloadRoom,
    reloadAnyRoom
  }
}
