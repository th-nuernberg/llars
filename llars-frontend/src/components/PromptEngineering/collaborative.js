import { ref, onMounted, onUnmounted, watch } from 'vue';
import { io } from 'socket.io-client';

export function useCollaborativeEditing(promptId, blocks) {
  const socket = ref(null);
  const collaborators = ref([]);
  const cursors = ref({});

  const initSocket = () => {
    socket.value = io(`${import.meta.env.VITE_API_BASE_URL}`);

    socket.value.emit('join_prompt', {
      promptId,
      username: localStorage.getItem('username') || 'Anonymous'
    });

    socket.value.on('collaborator_joined', (data) => {
      collaborators.value = data.collaborators;
    });

    socket.value.on('collaborator_left', (data) => {
      collaborators.value = data.collaborators;
    });

    socket.value.on('cursor_update', (data) => {
      if (data.userId !== socket.value.id) {
        cursors.value[data.userId] = data;
      }
    });

    socket.value.on('content_update', (data) => {
      if (data.userId !== socket.value.id) {
        const block = blocks.value.find(b => b.name === data.blockId);
        if (block) {
          block.content = data.content;
        }
      }
    });
  };

  const updateCursorPosition = (textareaEl, blockId) => {
    if (!textareaEl || !socket.value) return;

    const position = textareaEl.selectionStart;
    const cursorData = {
      blockId,
      position,
      userId: socket.value.id,
      timestamp: Date.now()
    };

    socket.value.emit('cursor_move', { promptId, ...cursorData });
  };

const handleTextChange = (blockId, content) => {
  if (!socket.value) return;

  // Stellen Sie sicher, dass nur der String-Wert gesendet wird
  const textContent = typeof content === 'object' ? content.target?.value : content;

  socket.value.emit('content_change', {
    promptId,
    blockId,
    content: textContent,
    userId: socket.value.id,
    timestamp: Date.now()
  });
};

  // Listen for changes in blocks
  watch(blocks, (newBlocks) => {
    if (socket.value) {
      socket.value.emit('blocks_update', {
        promptId,
        blocks: newBlocks,
        timestamp: Date.now()
      });
    }
  }, { deep: true });

  onMounted(() => {
    initSocket();
  });

  onUnmounted(() => {
    if (socket.value) {
      socket.value.disconnect();
    }
  });

  return {
    collaborators,
    cursors,
    updateCursorPosition,
    handleTextChange
  };
}
