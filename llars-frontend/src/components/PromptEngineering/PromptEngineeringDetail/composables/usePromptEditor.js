/**
 * Prompt Editor Composable
 *
 * Handles Quill editor initialization, cursor management, and highlighting.
 * Extracted from PromptEngineeringDetail.vue for better maintainability.
 */

import { ref, nextTick } from 'vue';
import Quill from 'quill';
import { QuillBinding } from 'y-quill';
import * as Y from 'yjs';

export function usePromptEditor(ydocRef, socketRef, roomIdRef) {
  // Editor state
  const editorsMap = ref(new Map());
  const editors = ref(new Map());
  const bindings = ref(new Map());
  const cursorsModules = ref(new Map());

  // Debounce utility
  const debounce = (fn, delay) => {
    let timeoutId;
    return (...args) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => fn(...args), delay);
    };
  };

  // Cursor update handler for remote users
  const updateCursor = (userId, cursor) => {
    // If cursor === null, remove cursor in all blocks
    if (!cursor) {
      cursorsModules.value.forEach((cursorsModule) => {
        cursorsModule.removeCursor(userId);
      });
      return;
    }

    const { blockId, range, username, color } = cursor;
    const cursorsModule = cursorsModules.value.get(blockId);
    const editor = editors.value.get(blockId);

    // If range === null, only remove cursor in that specific block
    if (!range) {
      if (cursorsModule) {
        cursorsModule.removeCursor(userId);
      }
      return;
    }

    // If valid range, update cursor
    if (cursorsModule && editor) {
      if (!cursorsModule.cursors().find(c => c.id === userId)) {
        cursorsModule.createCursor(userId, username, color);
      }

      const transformedRange = editor.getLength() < range.index
        ? { index: editor.getLength(), length: 0 }
        : range;

      cursorsModule.moveCursor(userId, transformedRange);
    }
  };

  // Remove cursor for a user from all blocks
  const removeUserCursor = (userId) => {
    cursorsModules.value.forEach(cursorsModule => {
      cursorsModule.removeCursor(userId);
    });
  };

  // Selection change handler
  const handleSelectionChange = (blockId) => {
    const debouncedEmit = debounce((range) => {
      if (socketRef.value?.connected) {
        socketRef.value.emit('cursor_update', {
          room: roomIdRef.value,
          blockId,
          range: range
            ? {
                index: range.index,
                length: range.length
              }
            : null
        });
      }
    }, 50);

    return (range, oldRange, source) => {
      if (source === 'user') {
        if (!range) {
          const cursorsModule = cursorsModules.value.get(blockId);
          if (cursorsModule && socketRef.value) {
            cursorsModule.removeCursor(socketRef.value.id);
          }
        }
        debouncedEmit(range);
      }
    };
  };

  // Initialize editor for a block
  const initializeEditor = async (block) => {
    await nextTick();

    const editorElement = editorsMap.value.get(block.id);
    if (!editorElement || editors.value.has(block.id)) {
      return;
    }

    const blocksMap = ydocRef.value.getMap('blocks');
    const blockMap = blocksMap.get(block.id);
    if (!blockMap) {
      console.error('Block map not found:', block.id);
      return;
    }

    let ytext = blockMap.get('content');
    if (!ytext) {
      ytext = new Y.Text();
      blockMap.set('content', ytext);

      const update = Y.encodeStateAsUpdate(ydocRef.value);
      if (socketRef.value?.connected) {
        socketRef.value.emit('sync_update', {
          room: roomIdRef.value,
          update: Array.from(update)
        });
      }
    }

    // Quill Editor with cursor settings
    const editor = new Quill(editorElement, {
      modules: {
        cursors: {
          transformOnTextChange: true,
          hideDelayMs: 5000,
          hideSpeedMs: 500,
          selectionChangeSource: 'api'
        },
        toolbar: [
          ['bold', 'italic', 'underline'],
          ['clean']
        ],
        history: {
          userOnly: true
        }
      },
      theme: 'snow',
      placeholder: `Start editing ${block.title}...`
    });

    // Flag for placeholder highlighting recursion prevention
    let inPlaceholderHighlight = false;

    // Highlight placeholders function
    function highlightPlaceholders() {
      if (inPlaceholderHighlight) return;
      inPlaceholderHighlight = true;
      try {
        const placeholder = '{{complete_email_history}}';
        editor.formatText(0, editor.getLength(), 'placeholder', false, Quill.sources.API);
        const text = editor.getText();
        let idx = text.indexOf(placeholder);
        while (idx !== -1) {
          editor.formatText(idx, placeholder.length, 'placeholder', true, Quill.sources.API);
          idx = text.indexOf(placeholder, idx + placeholder.length);
        }
      } finally {
        inPlaceholderHighlight = false;
      }
    }

    // Observe Yjs text for highlighting
    ytext.observe(() => {
      setTimeout(() => highlightPlaceholders(), 0);
    });

    // Store cursors module reference
    const cursorsModule = editor.getModule('cursors');
    cursorsModules.value.set(block.id, cursorsModule);

    // Yjs-Quill binding
    const binding = new QuillBinding(ytext, editor, null, {
      preserveCursor: true
    });

    // Initial highlighting
    highlightPlaceholders();

    // Selection change handler
    editor.on('selection-change', handleSelectionChange(block.id));

    // Text change handler
    editor.on('text-change', (delta, oldDelta, source) => {
      if (source === 'user') {
        ydocRef.value.transact(() => {
          const blocksMap2 = ydocRef.value.getMap('blocks');
          const blockMap2 = blocksMap2.get(block.id);
          blockMap2.get('content').applyDelta(delta);
          const update2 = Y.encodeStateAsUpdate(ydocRef.value);
          if (socketRef.value?.connected) {
            socketRef.value.emit('sync_update', {
              room: roomIdRef.value,
              update: Array.from(update2)
            });
          }
        });
      }
    });

    editors.value.set(block.id, editor);
    bindings.value.set(block.id, binding);
  };

  // Set editor element reference
  const setEditorRef = (el, blockId) => {
    if (el) {
      editorsMap.value.set(blockId, el);
    }
  };

  // Cleanup deleted blocks
  const cleanupDeletedBlocks = (deletedBlocks) => {
    deletedBlocks.forEach(block => {
      const binding = bindings.value.get(block.id);
      if (binding) {
        binding.destroy();
        bindings.value.delete(block.id);
      }

      editors.value.delete(block.id);
      editorsMap.value.delete(block.id);
      cursorsModules.value.delete(block.id);
    });
  };

  // Cleanup all editors
  const cleanupAllEditors = () => {
    bindings.value.forEach(binding => binding.destroy());
    editorsMap.value.clear();
    editors.value.clear();
    bindings.value.clear();
    cursorsModules.value.clear();
  };

  // Apply highlighting to all editors
  const applyHighlightingToAll = () => {
    editors.value.forEach(editor => {
      if (editor) {
        const text = editor.getText();
        const placeholder = '{{complete_email_history}}';
        let idx = text.indexOf(placeholder);
        while (idx !== -1) {
          editor.formatText(idx, placeholder.length, 'placeholder', true, Quill.sources.API);
          idx = text.indexOf(placeholder, idx + placeholder.length);
        }
      }
    });
  };

  return {
    // State
    editorsMap,
    editors,
    bindings,
    cursorsModules,

    // Methods
    updateCursor,
    removeUserCursor,
    initializeEditor,
    setEditorRef,
    cleanupDeletedBlocks,
    cleanupAllEditors,
    applyHighlightingToAll
  };
}
