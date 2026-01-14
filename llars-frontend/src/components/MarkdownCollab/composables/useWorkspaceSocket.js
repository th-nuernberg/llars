import { ref, onUnmounted, watch } from 'vue'
import { io } from 'socket.io-client'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

/**
 * Composable for workspace-level Socket.IO communication
 * Handles real-time tree updates (create, rename, delete, move)
 */
export function useWorkspaceSocket(workspaceId, options = {}) {
  const socket = ref(null)
  const isConnected = ref(false)
  const recentlyAddedNodeIds = ref(new Set())
  const socketioEnableWebsocket = String(import.meta.env.VITE_SOCKETIO_ENABLE_WEBSOCKET || '').toLowerCase() === 'true'
  const socketioTransports = socketioEnableWebsocket ? ['polling', 'websocket'] : ['polling']

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

  function connect() {
    if (socket.value?.connected) return

    socket.value = io(getSocketBaseUrl(), {
      path: '/collab/socket.io/',
      auth: {
        token: getAuthToken(),
        color: getCollabColor()
      },
      transports: socketioTransports,
      upgrade: socketioEnableWebsocket,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000
    })

    socket.value.on('connect', () => {
      isConnected.value = true
      console.log('[WorkspaceSocket] Verbunden')

      // Join the workspace room
      if (workspaceId.value) {
        socket.value.emit('join_workspace', { workspaceId: workspaceId.value })
      }
    })

    socket.value.on('disconnect', () => {
      isConnected.value = false
      console.log('[WorkspaceSocket] Verbindung getrennt')
    })

    socket.value.on('connect_error', (err) => {
      console.error('[WorkspaceSocket] Verbindungsfehler:', err.message)
      isConnected.value = false
    })

    // Listen for tree changes from other users
    socket.value.on('tree_node_created', (data) => {
      console.log('[WorkspaceSocket] Knoten von anderem Benutzer erstellt:', data)
      if (options.onNodeCreated) {
        // Mark as recently added for animation
        recentlyAddedNodeIds.value.add(data.node.id)
        setTimeout(() => {
          recentlyAddedNodeIds.value.delete(data.node.id)
        }, 2000)

        options.onNodeCreated(data)
      }
    })

    socket.value.on('tree_node_renamed', (data) => {
      console.log('[WorkspaceSocket] Knoten von anderem Benutzer umbenannt:', data)
      if (options.onNodeRenamed) {
        options.onNodeRenamed(data)
      }
    })

    socket.value.on('tree_node_deleted', (data) => {
      console.log('[WorkspaceSocket] Knoten von anderem Benutzer geloescht:', data)
      if (options.onNodeDeleted) {
        options.onNodeDeleted(data)
      }
    })

    socket.value.on('tree_node_moved', (data) => {
      console.log('[WorkspaceSocket] Knoten von anderem Benutzer verschoben:', data)
      if (options.onNodeMoved) {
        options.onNodeMoved(data)
      }
    })
  }

  function disconnect() {
    if (socket.value) {
      if (workspaceId.value) {
        socket.value.emit('leave_workspace', { workspaceId: workspaceId.value })
      }
      socket.value.disconnect()
      socket.value = null
    }
    isConnected.value = false
  }

  // Emit functions for broadcasting changes to other users
  function emitNodeCreated(node) {
    if (!socket.value?.connected || !workspaceId.value) return
    socket.value.emit('tree_node_created', {
      workspaceId: workspaceId.value,
      node
    })
  }

  function emitNodeRenamed(nodeId, newTitle) {
    if (!socket.value?.connected || !workspaceId.value) return
    socket.value.emit('tree_node_renamed', {
      workspaceId: workspaceId.value,
      nodeId,
      newTitle
    })
  }

  function emitNodeDeleted(nodeId) {
    if (!socket.value?.connected || !workspaceId.value) return
    socket.value.emit('tree_node_deleted', {
      workspaceId: workspaceId.value,
      nodeId
    })
  }

  function emitNodeMoved(nodeId, newParentId, newOrderIndex) {
    if (!socket.value?.connected || !workspaceId.value) return
    socket.value.emit('tree_node_moved', {
      workspaceId: workspaceId.value,
      nodeId,
      newParentId,
      newOrderIndex
    })
  }

  // Watch for workspace ID changes
  watch(workspaceId, (newId, oldId) => {
    if (socket.value?.connected) {
      if (oldId) {
        socket.value.emit('leave_workspace', { workspaceId: oldId })
      }
      if (newId) {
        socket.value.emit('join_workspace', { workspaceId: newId })
      }
    }
  })

  // Cleanup on unmount
  onUnmounted(() => {
    disconnect()
  })

  return {
    socket,
    isConnected,
    recentlyAddedNodeIds,
    connect,
    disconnect,
    emitNodeCreated,
    emitNodeRenamed,
    emitNodeDeleted,
    emitNodeMoved
  }
}
