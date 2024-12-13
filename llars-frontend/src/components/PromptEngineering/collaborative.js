import { ref, onMounted, onUnmounted, watch } from 'vue';
import { io } from 'socket.io-client';

export function useCollaborativeEditing(promptId, blocks) {
  const socket = ref(null);
  const collaborators = ref([]);
  const cursors = ref({});
  const lastCursorPositions = ref({});

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
        const block = blocks.value.find(b => b.name === data.block_id);
        if (block) {
          const lastPosition = lastCursorPositions.value[data.block_id];
          if (lastPosition) {
            const oldContent = block.content;
            const newContent = data.content;

            // Calculate the new cursor position based on content changes
            const newPosition = calculateNewCursorPosition(
              oldContent,
              newContent,
              lastPosition.start,
              lastPosition.end
            );

            // Update the content
            block.content = data.content;

            // Restore cursor position after Vue updates the DOM
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
  };

  const calculateNewCursorPosition = (oldContent, newContent, oldStart, oldEnd) => {
    // Find the common prefix length
    let prefixLength = 0;
    const minLength = Math.min(oldContent.length, newContent.length);
    while (prefixLength < minLength && oldContent[prefixLength] === newContent[prefixLength]) {
      prefixLength++;
    }

    // Find the common suffix length
    let suffixLength = 0;
    while (
      suffixLength < minLength - prefixLength &&
      oldContent[oldContent.length - 1 - suffixLength] === newContent[newContent.length - 1 - suffixLength]
    ) {
      suffixLength++;
    }

    // Calculate the change in length
    const lengthDiff = newContent.length - oldContent.length;

    // Adjust cursor position based on where the change occurred
    let newStart = oldStart;
    let newEnd = oldEnd;

    if (oldStart > prefixLength) {
      // Cursor is after the change
      newStart += lengthDiff;
      newEnd += lengthDiff;
    }

    // Ensure positions are within bounds
    newStart = Math.max(0, Math.min(newStart, newContent.length));
    newEnd = Math.max(0, Math.min(newEnd, newContent.length));

    return { start: newStart, end: newEnd };
  };

  const updateCursorPosition = (textareaEl, block_id) => {
    if (!textareaEl || !socket.value) return;

    const position = textareaEl.selectionStart;
    const cursorData = {
      block_id,
      position,
      userId: socket.value.id,
      timestamp: Date.now()
    };

    // Save the current cursor position
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
      userId: socket.value.id,
      timestamp: Date.now()
    });
  };

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
