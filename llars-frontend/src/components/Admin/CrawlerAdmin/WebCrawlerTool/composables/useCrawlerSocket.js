/**
 * Crawler Socket Composable
 *
 * Handles Socket.IO connection for live crawler updates.
 * Extracted from WebCrawlerTool.vue for better maintainability.
 */

import { ref } from 'vue';
import { io } from 'socket.io-client';

const socketioEnableWebsocket = String(import.meta.env.VITE_SOCKETIO_ENABLE_WEBSOCKET || '').toLowerCase() === 'true';
const socketioTransports = socketioEnableWebsocket ? ['polling', 'websocket'] : ['polling'];

export function useCrawlerSocket(callbacks = {}) {
  let socket = null;
  const socketConnected = ref(false);
  const isReconnecting = ref(false);
  const reconnectionFailed = ref(false);
  let reconnectAttempts = 0;
  const maxReconnectAttempts = 10;

  const initSocket = () => {
    if (socket && socket.connected) return socket;

    // Clean up old socket
    if (socket) {
      socket.disconnect();
      socket = null;
    }

    const baseUrl = window.location.origin;

    socket = io(baseUrl, {
      path: '/socket.io',
      transports: socketioTransports,
      upgrade: socketioEnableWebsocket,
      reconnection: true,
      reconnectionAttempts: maxReconnectAttempts,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000,
      forceNew: true
    });

    socket.on('connect', () => {
      console.log('[Crawler Socket] Connected:', socket.id);
      socketConnected.value = true;
      isReconnecting.value = false;
      reconnectionFailed.value = false;
      reconnectAttempts = 0;

      if (callbacks.onConnect) {
        callbacks.onConnect();
      }
    });

    socket.on('disconnect', (reason) => {
      console.log('[Crawler Socket] Disconnected:', reason);
      socketConnected.value = false;
      if (reason !== 'io client disconnect') {
        isReconnecting.value = true;
      }
    });

    socket.on('connect_error', (error) => {
      console.warn('[Crawler Socket] Connection error:', error.message);
      reconnectAttempts++;
      isReconnecting.value = true;
      if (reconnectAttempts >= maxReconnectAttempts) {
        console.error('[Crawler Socket] Max reconnection attempts reached');
        isReconnecting.value = false;
        reconnectionFailed.value = true;
      }
    });

    // Crawler-specific events
    socket.on('crawler:joined', (data) => {
      console.log('[Crawler Socket] Joined session:', data);
    });

    socket.on('crawler:progress', (data) => {
      console.log('[Crawler Socket] Progress:', data);
      if (callbacks.onProgress) {
        callbacks.onProgress(data);
      }
    });

    socket.on('crawler:page_crawled', (data) => {
      console.log('[Crawler Socket] Page crawled:', data);
      if (callbacks.onPageCrawled) {
        callbacks.onPageCrawled(data);
      }
    });

    socket.on('crawler:complete', (data) => {
      console.log('[Crawler Socket] Complete:', data);
      if (callbacks.onComplete) {
        callbacks.onComplete(data);
      }
    });

    socket.on('crawler:error', (data) => {
      console.error('[Crawler Socket] Error:', data);
      if (callbacks.onError) {
        callbacks.onError(data);
      }
    });

    socket.on('crawler:status', (data) => {
      console.log('[Crawler Socket] Status response:', data);
      if (callbacks.onStatus) {
        callbacks.onStatus(data);
      }
    });

    socket.on('crawler:jobs_list', (data) => {
      console.log('[Crawler Socket] Initial jobs list received:', data.jobs?.length || 0, 'jobs');
      if (callbacks.onJobsList) {
        callbacks.onJobsList(data.jobs);
      }
    });

    socket.on('crawler:jobs_updated', (data) => {
      console.log('[Crawler Socket] Jobs updated:', data.jobs?.length || 0, 'jobs');
      if (callbacks.onJobsUpdated) {
        callbacks.onJobsUpdated(data.jobs);
      }
    });

    return socket;
  };

  const subscribeToJobUpdates = () => {
    if (socket && socket.connected) {
      socket.emit('crawler:subscribe_jobs');
    } else if (socket) {
      socket.once('connect', () => {
        socket.emit('crawler:subscribe_jobs');
      });
    }
  };

  const joinSession = (jobId) => {
    if (socket) {
      socket.emit('crawler:join_session', { session_id: jobId });
      socket.emit('crawler:get_status', { session_id: jobId });
    }
  };

  const leaveSession = (jobId) => {
    if (socket) {
      socket.emit('crawler:leave_session', { session_id: jobId });
    }
  };

  const retryConnection = () => {
    reconnectionFailed.value = false;
    reconnectAttempts = 0;
    if (socket) {
      socket.disconnect();
      socket = null;
    }
    initSocket();
    subscribeToJobUpdates();
  };

  const disconnect = () => {
    if (socket) {
      socket.emit('crawler:unsubscribe_jobs');
      socket.disconnect();
      socket = null;
    }
  };

  const getSocket = () => socket;

  return {
    // State
    socketConnected,
    isReconnecting,
    reconnectionFailed,

    // Methods
    initSocket,
    subscribeToJobUpdates,
    joinSession,
    leaveSession,
    retryConnection,
    disconnect,
    getSocket
  };
}
