/**
 * Prompt Blocks Composable
 *
 * Handles block management: creation, deletion, sorting, and title editing.
 * Extracted from PromptEngineeringDetail.vue for better maintainability.
 */

import { ref, computed } from 'vue';
import * as Y from 'yjs';

export function usePromptBlocks(ydocRef, socketRef, roomIdRef) {
  // State
  const blocks = ref([]);
  const showAddBlockDialog = ref(false);
  const newBlockName = ref('');
  const showDeleteBlockDialog = ref(false);
  const blockToDelete = ref(null);
  const editingBlockId = ref(null);
  const editingBlockTitle = ref('');

  // JSON Upload
  const showUploadChoiceDialog = ref(false);
  const pendingJsonData = ref(null);

  // Sorted blocks computed
  const sortedBlocks = computed({
    get: () => {
      return [...blocks.value].sort((a, b) => a.position - b.position);
    },
    set: (newValue) => {
      // Update positions in blocks.value based on new order
      newValue.forEach((block, index) => {
        const originalBlock = blocks.value.find(b => b.id === block.id);
        if (originalBlock) {
          originalBlock.position = index;
        }
      });

      // Update positions in ydoc
      if (ydocRef.value) {
        ydocRef.value.transact(() => {
          const blocksMap = ydocRef.value.getMap('blocks');
          newValue.forEach((block, index) => {
            const blockMap = blocksMap.get(block.id);
            if (blockMap) {
              blockMap.set('position', index);
            }
          });
        });

        // Sync changes with other clients
        const update = Y.encodeStateAsUpdate(ydocRef.value);
        if (socketRef.value?.connected) {
          socketRef.value.emit('sync_update', {
            room: roomIdRef.value,
            update: Array.from(update)
          });
        }
      }
    }
  });

  // Dialog management
  const closeAddBlockDialog = () => {
    showAddBlockDialog.value = false;
    newBlockName.value = '';
  };

  const closeDeleteBlockDialog = () => {
    showDeleteBlockDialog.value = false;
    blockToDelete.value = null;
  };

  const openDeleteBlockDialog = (block) => {
    blockToDelete.value = block;
    showDeleteBlockDialog.value = true;
  };

  // Block creation
  const createBlock = (showSnackbar) => {
    const blockName = newBlockName.value.trim();
    if (!blockName) return;
    if (!ydocRef.value) return;

    ydocRef.value.transact(() => {
      const blocksMap = ydocRef.value.getMap('blocks');

      if (blocksMap.has(blockName)) {
        showSnackbar(`Block "${blockName}" existiert bereits!`);
        return;
      }

      let maxPosition = 0;
      blocksMap.forEach((blockMap) => {
        const pos = blockMap.get('position');
        if (pos > maxPosition) {
          maxPosition = pos;
        }
      });

      const newBlockMap = new Y.Map();
      newBlockMap.set('title', blockName);
      newBlockMap.set('position', maxPosition + 1);

      const ytext = new Y.Text();
      newBlockMap.set('content', ytext);

      blocksMap.set(blockName, newBlockMap);

      const update = Y.encodeStateAsUpdate(ydocRef.value);
      if (socketRef.value?.connected) {
        socketRef.value.emit('sync_update', {
          room: roomIdRef.value,
          update: Array.from(update)
        });
      }
    });

    showSnackbar(`Block "${blockName}" wurde hinzugefügt!`);
    closeAddBlockDialog();
  };

  // Block deletion
  const confirmDeleteBlock = (showSnackbar) => {
    if (!blockToDelete.value || !ydocRef.value) {
      closeDeleteBlockDialog();
      return;
    }

    const blockId = blockToDelete.value.id;

    ydocRef.value.transact(() => {
      const blocksMap = ydocRef.value.getMap('blocks');
      if (blocksMap.has(blockId)) {
        blocksMap.delete(blockId);

        const update = Y.encodeStateAsUpdate(ydocRef.value);
        if (socketRef.value?.connected) {
          socketRef.value.emit('sync_update', {
            room: roomIdRef.value,
            update: Array.from(update)
          });
        }
      }
    });

    showSnackbar(`Block "${blockToDelete.value.title}" wurde gelöscht!`);
    closeDeleteBlockDialog();
  };

  // Title editing
  const startEditBlockTitle = (block) => {
    editingBlockId.value = block.id;
    editingBlockTitle.value = block.title;
  };

  const saveBlockTitle = (block, showSnackbar) => {
    const newTitle = editingBlockTitle.value.trim();
    const oldTitle = block.title;

    if (!newTitle || newTitle === oldTitle) {
      editingBlockId.value = null;
      editingBlockTitle.value = '';
      return;
    }

    if (!ydocRef.value) {
      console.error('No Y.Doc available to update block title');
      return;
    }

    ydocRef.value.transact(() => {
      const blocksMap = ydocRef.value.getMap('blocks');
      const blockMap = blocksMap.get(block.id);
      if (blockMap) {
        blockMap.set('title', newTitle);

        const update = Y.encodeStateAsUpdate(ydocRef.value);
        if (socketRef.value?.connected) {
          socketRef.value.emit('sync_update', {
            room: roomIdRef.value,
            update: Array.from(update)
          });
        }
      }
    });

    editingBlockId.value = null;
    editingBlockTitle.value = '';
    showSnackbar(`Titel geändert zu "${newTitle}"!`);
  };

  // JSON Upload handlers
  const onJsonFileSelected = (jsonData) => {
    pendingJsonData.value = jsonData;
    showUploadChoiceDialog.value = true;
  };

  const handleJsonUpload = (jsonData, showSnackbar) => {
    if (!ydocRef.value) return;

    ydocRef.value.transact(() => {
      const blocksMap = ydocRef.value.getMap('blocks');

      let maxPosition = 0;
      blocksMap.forEach((blockMap) => {
        const pos = blockMap.get('position');
        if (pos > maxPosition) {
          maxPosition = pos;
        }
      });

      Object.entries(jsonData).forEach(([blockName, blockContent], idx) => {
        if (blocksMap.has(blockName)) {
          showSnackbar(`Block "${blockName}" existiert bereits! Übersprungen.`);
          return;
        }

        const newBlockMap = new Y.Map();
        newBlockMap.set('title', blockName);
        newBlockMap.set('position', maxPosition + idx + 1);

        const ytext = new Y.Text();
        ytext.insert(0, blockContent);
        newBlockMap.set('content', ytext);

        blocksMap.set(blockName, newBlockMap);
      });

      const update = Y.encodeStateAsUpdate(ydocRef.value);
      if (socketRef.value?.connected) {
        socketRef.value.emit('sync_update', {
          room: roomIdRef.value,
          update: Array.from(update)
        });
      }
    });

    showSnackbar('JSON-Datei erfolgreich verarbeitet!');
  };

  const overrideJsonBlocks = (showSnackbar) => {
    if (!pendingJsonData.value) return;

    if (ydocRef.value) {
      ydocRef.value.transact(() => {
        const blocksMap = ydocRef.value.getMap('blocks');
        blocksMap.forEach((val, key) => {
          blocksMap.delete(key);
        });

        const update = Y.encodeStateAsUpdate(ydocRef.value);
        if (socketRef.value?.connected) {
          socketRef.value.emit('sync_update', {
            room: roomIdRef.value,
            update: Array.from(update)
          });
        }
      });
    }

    handleJsonUpload(pendingJsonData.value, showSnackbar);

    showUploadChoiceDialog.value = false;
    pendingJsonData.value = null;
  };

  const appendJsonBlocks = (showSnackbar) => {
    if (!pendingJsonData.value) return;
    handleJsonUpload(pendingJsonData.value, showSnackbar);

    showUploadChoiceDialog.value = false;
    pendingJsonData.value = null;
  };

  const cancelJsonUpload = () => {
    showUploadChoiceDialog.value = false;
    pendingJsonData.value = null;
  };

  // Process Y.Doc to local blocks array
  const processYDoc = () => {
    if (!ydocRef.value) return;

    const blocksMap = ydocRef.value.getMap('blocks');
    const newBlocks = [];

    blocksMap.forEach((value, key) => {
      newBlocks.push({
        id: key,
        title: value.get('title'),
        position: value.get('position'),
        content: value.get('content')
      });
    });

    blocks.value = newBlocks;
  };

  return {
    // State
    blocks,
    sortedBlocks,
    showAddBlockDialog,
    newBlockName,
    showDeleteBlockDialog,
    blockToDelete,
    editingBlockId,
    editingBlockTitle,
    showUploadChoiceDialog,

    // Methods
    closeAddBlockDialog,
    closeDeleteBlockDialog,
    openDeleteBlockDialog,
    createBlock,
    confirmDeleteBlock,
    startEditBlockTitle,
    saveBlockTitle,
    onJsonFileSelected,
    overrideJsonBlocks,
    appendJsonBlocks,
    cancelJsonUpload,
    processYDoc
  };
}
