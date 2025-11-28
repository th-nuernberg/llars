/**
 * Prompt Socket Composable
 *
 * Handles Socket.IO connection for real-time collaboration.
 * Extracted from PromptEngineeringDetail.vue for better maintainability.
 */

import { ref, nextTick } from 'vue';
import { io } from 'socket.io-client';
import * as Y from 'yjs';

export function usePromptSocket(roomIdRef, username, ydocRef, processYDoc, updateCursor) {
  const socket = ref(null);
  const users = ref({});

  const initializeSocket = () => {
    socket.value = io(import.meta.env.VITE_API_BASE_URL, {
      path: '/collab/socket.io/',
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000
    });

    socket.value.on('connect', () => {
      console.log('Connected to server');
      socket.value.emit('join_room', {
        room: roomIdRef.value,
        username
      });
    });

    socket.value.on('snapshot_document', (fullUpdate) => {
      Y.applyUpdate(ydocRef.value, new Uint8Array(fullUpdate));
      processYDoc();
    });

    socket.value.on('sync_update', ({ update }) => {
      Y.applyUpdate(ydocRef.value, new Uint8Array(update));
      processYDoc();
    });

    socket.value.on('room_state', (state) => {
      users.value = state.users;
      nextTick(() => {
        Object.entries(state.cursors).forEach(([userId, cursor]) => {
          updateCursor(userId, cursor);
        });
      });
    });

    socket.value.on('user_joined', ({ userId, username, color }) => {
      users.value[userId] = { username, color };
    });

    socket.value.on('user_left', ({ userId }) => {
      delete users.value[userId];
      // Note: cursor removal is handled by the editor composable
    });

    socket.value.on('cursor_updated', ({ userId, cursor }) => {
      nextTick(() => updateCursor(userId, cursor));
    });

    socket.value.on('disconnect', () => {
      console.log('Disconnected from server');
    });

    return socket.value;
  };

  const disconnectSocket = () => {
    if (socket.value) {
      socket.value.disconnect();
      socket.value = null;
    }
  };

  return {
    socket,
    users,
    initializeSocket,
    disconnectSocket
  };
}
