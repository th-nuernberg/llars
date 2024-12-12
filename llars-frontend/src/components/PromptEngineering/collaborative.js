// collaborative.js
import { ref, onMounted, onUnmounted } from 'vue';
import { io } from 'socket.io-client';

export function useCollaborativeEditing(promptId, blocks) {
  const socket = io(`${import.meta.env.VITE_API_BASE_URL}`);
  const collaborators = ref([]);
  const cursors = ref({});

  const updateCursorPosition = (textareaEl, blockId) => {
    if (!textareaEl) return;
    const position = textareaEl.selectionStart;
    const cursorData = {
      blockId,
      position,
      userId: socket.id,
      timestamp: Date.now()
    };
    socket.emit('cursor_move', { promptId, ...cursorData });
  };

  const handleCursorUpdate = (data) => {
    if (data.userId === socket.id) return;
    cursors.value[data.userId] = data;
  };

  const handleTextChange = (blockId, newContent) => {
    socket.emit('content_change', {
      promptId,
      blockId,
      content: newContent,
      timestamp: Date.now()
    });
  };

  const handleIncomingChange = (data) => {
    const block = blocks.value.find(b => b.name === data.blockId);
    if (block) {
      block.content = data.content;
    }
  };

  const joinSession = () => {
    socket.emit('join_prompt', { promptId });
  };

  const handleCollaboratorJoin = (data) => {
    collaborators.value = data.collaborators;
  };

  onMounted(() => {
    socket.on('cursor_update', handleCursorUpdate);
    socket.on('content_update', handleIncomingChange);
    socket.on('collaborator_joined', handleCollaboratorJoin);
    socket.on('collaborator_left', handleCollaboratorJoin);
    joinSession();
  });

  onUnmounted(() => {
    socket.off('cursor_update', handleCursorUpdate);
    socket.off('content_update', handleIncomingChange);
    socket.off('collaborator_joined', handleCollaboratorJoin);
    socket.off('collaborator_left', handleCollaboratorJoin);
    socket.disconnect();
  });

  return {
    collaborators,
    cursors,
    updateCursorPosition,
    handleTextChange
  };
}

