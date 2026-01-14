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
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage';
import { logI18n } from '@/utils/logI18n';

// Connection state
const isConnected = ref(false);
const connectionError = ref(null);

// Socket instance
let socket = null;
let reconnectOnVisible = false;

const socketioEnvFlag = String(import.meta.env.VITE_SOCKETIO_ENABLE_WEBSOCKET || '').toLowerCase();
const autoEnableWebsocket = socketioEnvFlag === '' && typeof window !== 'undefined' && window.location.protocol === 'https:';
const socketioEnableWebsocket = socketioEnvFlag === 'true' || autoEnableWebsocket;
const socketioTransports = socketioEnableWebsocket ? ['websocket'] : ['polling'];
const socketioUpgrade = socketioEnableWebsocket && socketioTransports.includes('polling');

const getSocketBaseUrl = () => {
  if (typeof window === 'undefined') return import.meta.env.VITE_API_BASE_URL || '';
  const rawBase = import.meta.env.VITE_API_BASE_URL || window.location.origin;
  const trimmed = String(rawBase || '').replace(/\/+$/, '');
  if (trimmed.endsWith('/api')) {
    return trimmed.slice(0, -4);
  }
  return trimmed || window.location.origin;
};

const getSocketQuery = () => {
  const query = {};
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token);
  if (token) {
    query.token = token;
  }
  if (typeof window !== 'undefined') {
    const username = window.localStorage.getItem('username');
    if (username) {
      query.username = username;
    }
  }
  return query;
};

/**
 * Create or get the Socket.IO connection
 * @returns {Socket} Socket.IO instance
 */
export function getSocket() {
  // Return existing socket if it exists (even if not connected - it will reconnect)
  if (socket) {
    const nextQuery = getSocketQuery();
    const currentQuery = socket.io?.opts?.query || {};
    const shouldUpdateQuery = Object.keys(nextQuery).some((key) => nextQuery[key] !== currentQuery[key]);

    if (shouldUpdateQuery && socket.io?.opts) {
      socket.io.opts.query = { ...currentQuery, ...nextQuery };
      if (socket.connected) {
        socket.disconnect();
        socket.connect();
      }
    }

    // If socket exists but disconnected, trigger reconnect
    if (!socket.connected) {
      logI18n('log', 'logs.socketService.reconnecting');
      socket.connect();
    }
    return socket;
  }

  const baseUrl = getSocketBaseUrl();
  logI18n('log', 'logs.socketService.creatingConnection', baseUrl);

  socket = io(baseUrl, {
    transports: socketioTransports,
    upgrade: socketioUpgrade,
    reconnection: true,
    reconnectionAttempts: Infinity,  // Keep trying to reconnect
    reconnectionDelay: 1000,
    reconnectionDelayMax: 10000,
    timeout: 30000,  // Increased connection timeout
    // Prevent connection attempts when page is hidden
    autoConnect: document.visibilityState !== 'hidden',
    query: getSocketQuery(),
    // Increased ping timeout to match server (120s)
    // This prevents premature disconnections during long LLM streams
    pingTimeout: 120000,  // 2 minutes - matches server config
    pingInterval: 30000,  // 30 seconds - matches server config
  });

  // Connection handlers
  socket.on('connect', () => {
    logI18n('log', 'logs.socketService.connected');
    isConnected.value = true;
    connectionError.value = null;
  });

  socket.on('disconnect', (reason) => {
    logI18n('log', 'logs.socketService.disconnected', reason);
    isConnected.value = false;

    // If disconnected due to transport close (suspension), mark for reconnect
    if (reason === 'transport close' || reason === 'transport error') {
      reconnectOnVisible = true;
    }
  });

  socket.on('connect_error', (error) => {
    logI18n('warn', 'logs.socketService.connectionError', error.message);
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
    logI18n('log', 'logs.socketService.tabVisible');

    // Reconnect if needed
    if (socket && (!socket.connected || reconnectOnVisible)) {
      logI18n('log', 'logs.socketService.reconnectOnVisible');
      reconnectOnVisible = false;

      // Small delay to allow browser to stabilize
      setTimeout(() => {
        if (socket && !socket.connected) {
          socket.connect();
        }
      }, 100);
    }
  } else {
    logI18n('log', 'logs.socketService.tabHidden');
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
    logI18n('log', 'logs.socketService.cleanupBeforeUnload');
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
