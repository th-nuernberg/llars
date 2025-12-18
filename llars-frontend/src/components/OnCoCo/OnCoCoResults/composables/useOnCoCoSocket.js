/**
 * OnCoCo Socket Composable
 *
 * Handles Socket.IO connection and events for OnCoCo analysis live updates.
 * Extracted from OnCoCoResults.vue for better maintainability.
 */

import { ref } from 'vue';
import { io } from 'socket.io-client';

const socketioEnableWebsocket = String(import.meta.env.VITE_SOCKETIO_ENABLE_WEBSOCKET || '').toLowerCase() === 'true';
const socketioTransports = socketioEnableWebsocket ? ['polling', 'websocket'] : ['polling'];

export function useOnCoCoSocket(analysisId, callbacks = {}) {
  let socket = null;
  const connected = ref(false);

  const setupSocket = () => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL;
    socket = io(baseUrl, {
      transports: socketioTransports,
      upgrade: socketioEnableWebsocket,
      reconnection: true,
      reconnectionDelay: 1000,
    });

    socket.on('connect', () => {
      console.log('[OnCoCo Socket] Connected');
      connected.value = true;
      socket.emit('oncoco:join_analysis', { analysis_id: parseInt(analysisId.value) });
    });

    socket.on('oncoco:joined', (data) => {
      console.log('[OnCoCo Socket] Joined room:', data);
    });

    socket.on('oncoco:progress', (data) => {
      console.log('[OnCoCo Socket] Progress update:', data);
      if (callbacks.onProgress) {
        callbacks.onProgress(data);
      }
    });

    socket.on('oncoco:complete', async (data) => {
      console.log('[OnCoCo Socket] Analysis complete:', data);
      if (data.analysis_id === parseInt(analysisId.value)) {
        if (callbacks.onComplete) {
          callbacks.onComplete(data);
        }
      }
    });

    socket.on('oncoco:error', (data) => {
      console.error('[OnCoCo Socket] Error:', data);
      if (callbacks.onError) {
        callbacks.onError(data);
      }
    });

    socket.on('disconnect', () => {
      console.log('[OnCoCo Socket] Disconnected');
      connected.value = false;
    });

    return socket;
  };

  const cleanupSocket = () => {
    if (socket) {
      socket.emit('oncoco:leave_analysis', { analysis_id: parseInt(analysisId.value) });
      socket.disconnect();
      socket = null;
      connected.value = false;
    }
  };

  const getSocket = () => socket;

  return {
    connected,
    setupSocket,
    cleanupSocket,
    getSocket
  };
}
