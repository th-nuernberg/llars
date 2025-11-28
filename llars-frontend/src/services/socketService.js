/**
 * Socket.IO Service with graceful handling of browser suspension
 *
 * Handles:
 * - Automatic reconnection on tab visibility change
 * - Graceful disconnection before page unload
 * - Connection state management
 */

import { io } from 'socket.io-client';
import { ref, readonly } from 'vue';

// Connection state
const isConnected = ref(false);
const connectionError = ref(null);

// Socket instance
let socket = null;
let reconnectOnVisible = false;

/**
 * Create or get the Socket.IO connection
 * @returns {Socket} Socket.IO instance
 */
export function getSocket() {
  // Return existing socket if it exists (even if not connected - it will reconnect)
  if (socket) {
    // If socket exists but disconnected, trigger reconnect
    if (!socket.connected) {
      console.log('[SocketService] Socket exists but disconnected, reconnecting...');
      socket.connect();
    }
    return socket;
  }

  const baseUrl = import.meta.env.VITE_API_BASE_URL;
  console.log('[SocketService] Creating new socket connection to:', baseUrl);

  socket = io(baseUrl, {
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: Infinity,  // Keep trying to reconnect
    reconnectionDelay: 1000,
    reconnectionDelayMax: 10000,
    timeout: 30000,  // Increased connection timeout
    // Prevent connection attempts when page is hidden
    autoConnect: document.visibilityState !== 'hidden',
    // Increased ping timeout to match server (120s)
    // This prevents premature disconnections during long LLM streams
    pingTimeout: 120000,  // 2 minutes - matches server config
    pingInterval: 30000,  // 30 seconds - matches server config
  });

  // Connection handlers
  socket.on('connect', () => {
    console.log('[SocketService] Connected');
    isConnected.value = true;
    connectionError.value = null;
  });

  socket.on('disconnect', (reason) => {
    console.log('[SocketService] Disconnected:', reason);
    isConnected.value = false;

    // If disconnected due to transport close (suspension), mark for reconnect
    if (reason === 'transport close' || reason === 'transport error') {
      reconnectOnVisible = true;
    }
  });

  socket.on('connect_error', (error) => {
    console.warn('[SocketService] Connection error:', error.message);
    connectionError.value = error.message;
    isConnected.value = false;
  });

  // Setup visibility change handler
  setupVisibilityHandler();

  // Setup beforeunload handler for graceful cleanup
  setupUnloadHandler();

  return socket;
}

/**
 * Handle page visibility changes (tab switching, screen lock, etc.)
 */
function setupVisibilityHandler() {
  if (typeof document === 'undefined') return;

  // Remove existing listener to prevent duplicates
  document.removeEventListener('visibilitychange', handleVisibilityChange);
  document.addEventListener('visibilitychange', handleVisibilityChange);
}

function handleVisibilityChange() {
  if (document.visibilityState === 'visible') {
    console.log('[SocketService] Tab became visible');

    // Reconnect if needed
    if (socket && (!socket.connected || reconnectOnVisible)) {
      console.log('[SocketService] Reconnecting after visibility change...');
      reconnectOnVisible = false;

      // Small delay to allow browser to stabilize
      setTimeout(() => {
        if (socket && !socket.connected) {
          socket.connect();
        }
      }, 100);
    }
  } else {
    console.log('[SocketService] Tab became hidden');
    // Optionally disconnect to save resources (uncomment if desired)
    // if (socket && socket.connected) {
    //   socket.disconnect();
    //   reconnectOnVisible = true;
    // }
  }
}

/**
 * Graceful cleanup before page unload
 */
function setupUnloadHandler() {
  if (typeof window === 'undefined') return;

  window.removeEventListener('beforeunload', handleBeforeUnload);
  window.addEventListener('beforeunload', handleBeforeUnload);
}

function handleBeforeUnload() {
  if (socket) {
    console.log('[SocketService] Cleaning up before unload');
    socket.disconnect();
  }
}

/**
 * Disconnect and cleanup
 */
export function disconnectSocket() {
  if (socket) {
    socket.disconnect();
    socket = null;
    isConnected.value = false;
  }
}

/**
 * Manually trigger reconnection
 */
export function reconnect() {
  if (socket) {
    if (!socket.connected) {
      socket.connect();
    }
  } else {
    getSocket();
  }
}

/**
 * Get connection state (readonly)
 */
export function useSocketState() {
  return {
    isConnected: readonly(isConnected),
    connectionError: readonly(connectionError),
  };
}

export default {
  getSocket,
  disconnectSocket,
  reconnect,
  useSocketState,
};
