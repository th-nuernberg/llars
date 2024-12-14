// collaborative.js
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { io } from 'socket.io-client';

export function useCollaborativeEditing(promptId, blocks) {
  const socket = ref(null);
  const collaborators = ref([]);
  const cursors = ref({});
  const lastCursorPositions = ref({});
  const isBlockUpdateFromServer = ref(false);

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
      if (data.user_id !== socket.value.id) {
        cursors.value[data.user_id] = data;
      }
    });

    socket.value.on('content_update', (data) => {
      if (data.user_id !== socket.value.id) {
        const block = blocks.value.find(b => b.name === data.block_id);
        if (block) {
          const lastPosition = lastCursorPositions.value[data.block_id];
          if (lastPosition) {
            const oldContent = block.content;
            const newContent = data.content;

            const newPosition = calculateNewCursorPosition(
              oldContent,
              newContent,
              lastPosition.start,
              lastPosition.end
            );

            block.content = data.content;

            setTimeout(() => {
              const textarea = document.querySelector(`[data-block-id="${data.block_id}"]`)?.querySelector('textarea');
              if (textarea) {
                textarea.setSelectionRange(newPosition.start, newPosition.end);
                textarea.focus();
              }
            }, 0);
          } else {
            block.content = data.content;
          }
        }
      }
    });

    // Add new listener for block updates
    socket.value.on('blocks_update', (data) => {
      if (data.user_id !== socket.value.id) {
        isBlockUpdateFromServer.value = true;
        blocks.value = data.blocks;
        setTimeout(() => {
          isBlockUpdateFromServer.value = false;
        }, 0);
      }
    });
  };

  // Existing helper functions...
  const calculateNewCursorPosition = (oldContent, newContent, oldStart, oldEnd) => {
    let prefixLength = 0;
    const minLength = Math.min(oldContent.length, newContent.length);
    while (prefixLength < minLength && oldContent[prefixLength] === newContent[prefixLength]) {
      prefixLength++;
    }

    let suffixLength = 0;
    while (
      suffixLength < minLength - prefixLength &&
      oldContent[oldContent.length - 1 - suffixLength] === newContent[newContent.length - 1 - suffixLength]
    ) {
      suffixLength++;
    }

    const lengthDiff = newContent.length - oldContent.length;

    let newStart = oldStart;
    let newEnd = oldEnd;

    if (oldStart > prefixLength) {
      newStart += lengthDiff;
      newEnd += lengthDiff;
    }

    newStart = Math.max(0, Math.min(newStart, newContent.length));
    newEnd = Math.max(0, Math.min(newEnd, newContent.length));

    return { start: newStart, end: newEnd };
  };

  const updateCursorPosition = (textareaEl, block_id) => {
    if (!textareaEl || !socket.value) return;

    const position = textareaEl.selectionStart;
    const username = localStorage.getItem('username') || 'Anonymous';

    const cursorData = {
      block_id,
      position,
      user_id: socket.value.id,
      username,
      timestamp: Date.now()
    };

    lastCursorPositions.value[block_id] = {
      start: textareaEl.selectionStart,
      end: textareaEl.selectionEnd
    };

    socket.value.emit('cursor_move', { promptId, ...cursorData });
  };

  const handleTextChange = (block_id, content) => {
    if (!socket.value) return;

    const textContent = typeof content === 'object' ? content.target?.value : content;

    socket.value.emit('content_change', {
      promptId,
      block_id,
      content: textContent,
      user_id: socket.value.id,
      timestamp: Date.now()
    });
  };

  // Add blocks update handler
  const handleBlocksUpdate = (newBlocks) => {
    if (!socket.value || isBlockUpdateFromServer.value) return;

    socket.value.emit('blocks_update', {
      promptId,
      blocks: newBlocks,
      user_id: socket.value.id,
      timestamp: Date.now()
    });
  };

  watch(blocks, (newBlocks) => {
    handleBlocksUpdate(newBlocks);
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
    handleTextChange,
    isBlockUpdateFromServer
  };
}
