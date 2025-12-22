import { ref, computed } from 'vue'
import * as Y from 'yjs'

export function usePromptBlocks(ydoc, roomId, socket, showMessage) {
  const blocks = ref([])

  // Sortierte Liste der Blocks
  const sortedBlocks = computed({
    get: () => {
      return [...blocks.value].sort((a, b) => a.position - b.position)
    },
    set: (newValue) => {
      // Update positions in blocks.value based on new order
      newValue.forEach((block, index) => {
        const originalBlock = blocks.value.find(b => b.id === block.id)
        if (originalBlock) {
          originalBlock.position = index
        }
      })

      // Update positions in ydoc
      // NOTE: autoSync in useYjsCollaboration handles broadcasting automatically
      if (ydoc.value) {
        ydoc.value.transact(() => {
          const blocksMap = ydoc.value.getMap('blocks')
          newValue.forEach((block, index) => {
            const blockMap = blocksMap.get(block.id)
            if (blockMap) {
              blockMap.set('position', index)
            }
          })
        })
      }
    }
  })

  // Alle Blocks in das lokale Array laden
  const processYDoc = () => {
    if (!ydoc.value) return

    const blocksMap = ydoc.value.getMap('blocks')
    const newBlocks = []

    blocksMap.forEach((value, key) => {
      newBlocks.push({
        id: key,
        title: value.get('title'),
        position: value.get('position'),
        content: value.get('content')
      })
    })

    blocks.value = newBlocks
  }

  // Neuen Block erstellen
  const createBlock = (blockName) => {
    const trimmedName = blockName.trim()
    if (!trimmedName) return false
    if (!ydoc.value) return false

    let success = false

    // NOTE: autoSync in useYjsCollaboration handles broadcasting automatically
    ydoc.value.transact(() => {
      const blocksMap = ydoc.value.getMap('blocks')

      // Prüfen, ob der Blockname schon existiert
      if (blocksMap.has(trimmedName)) {
        showMessage(`Block "${trimmedName}" existiert bereits!`)
        return
      }

      let maxPosition = 0
      blocksMap.forEach((blockMap) => {
        const pos = blockMap.get('position')
        if (pos > maxPosition) {
          maxPosition = pos
        }
      })

      // Neuen Block anlegen
      const newBlockMap = new Y.Map()
      newBlockMap.set('title', trimmedName)
      newBlockMap.set('position', maxPosition + 1)

      // Leerer Y.Text
      const ytext = new Y.Text()
      newBlockMap.set('content', ytext)

      // In blocksMap einfügen
      blocksMap.set(trimmedName, newBlockMap)

      success = true
    })

    if (success) {
      showMessage(`Block "${trimmedName}" wurde hinzugefügt!`)
    }

    return success
  }

  // Block löschen
  const deleteBlock = (block) => {
    if (!block || !ydoc.value) return false

    const blockId = block.id

    // NOTE: autoSync in useYjsCollaboration handles broadcasting automatically
    ydoc.value.transact(() => {
      const blocksMap = ydoc.value.getMap('blocks')
      if (blocksMap.has(blockId)) {
        blocksMap.delete(blockId)
      }
    })

    showMessage(`Block "${block.title}" wurde gelöscht!`)
    return true
  }

  // Block-Titel speichern
  const saveBlockTitle = (block, newTitle) => {
    const trimmedTitle = newTitle.trim()
    const oldTitle = block.title

    // If the new title is empty or unchanged, just return false
    if (!trimmedTitle || trimmedTitle === oldTitle) {
      return false
    }

    if (!ydoc.value) {
      console.error('No Y.Doc available to update block title')
      return false
    }

    // Update the Y.Doc
    // NOTE: autoSync in useYjsCollaboration handles broadcasting automatically
    ydoc.value.transact(() => {
      const blocksMap = ydoc.value.getMap('blocks')
      const blockMap = blocksMap.get(block.id)
      if (blockMap) {
        blockMap.set('title', trimmedTitle)
      }
    })

    showMessage(`Titel geändert zu "${trimmedTitle}"!`)
    return true
  }

  // JSON-Datei verarbeiten (Blocks hinzufügen)
  // NOTE: autoSync in useYjsCollaboration handles broadcasting automatically
  const handleJsonUpload = (jsonData, override = false) => {
    if (!ydoc.value) return false

    ydoc.value.transact(() => {
      const blocksMap = ydoc.value.getMap('blocks')

      // Wenn override, alle vorhandenen Blocks löschen
      if (override) {
        blocksMap.forEach((val, key) => {
          blocksMap.delete(key)
        })
      }

      let maxPosition = 0
      blocksMap.forEach((blockMap) => {
        const pos = blockMap.get('position')
        if (pos > maxPosition) {
          maxPosition = pos
        }
      })

      // Iteriere über Keys und Values im jsonData
      Object.entries(jsonData).forEach(([blockName, blockContent], idx) => {
        // Existiert der Block schon?
        if (blocksMap.has(blockName)) {
          showMessage(`Block "${blockName}" existiert bereits! Übersprungen.`)
          return
        }

        const newBlockMap = new Y.Map()
        newBlockMap.set('title', blockName)
        newBlockMap.set('position', maxPosition + idx + 1)

        // Neuen Text anlegen
        const ytext = new Y.Text()
        ytext.insert(0, blockContent)
        newBlockMap.set('content', ytext)

        blocksMap.set(blockName, newBlockMap)
      })
    })

    showMessage('JSON-Datei erfolgreich verarbeitet!')
    return true
  }

  // Prompt zusammenstellen
  const assemblePrompt = () => {
    return sortedBlocks.value.map(b => b.content.toString()).join('\n\n')
  }

  return {
    blocks,
    sortedBlocks,
    processYDoc,
    createBlock,
    deleteBlock,
    saveBlockTitle,
    handleJsonUpload,
    assemblePrompt
  }
}
