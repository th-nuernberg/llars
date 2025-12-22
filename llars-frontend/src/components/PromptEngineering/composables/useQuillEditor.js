import { ref, nextTick } from 'vue'
import Quill from 'quill'
import { QuillBinding } from 'y-quill'
import * as Y from 'yjs'

export function useQuillEditor(ydoc, socket, roomId) {
  const editorsMap = ref(new Map())
  const editors = ref(new Map())
  const bindings = ref(new Map())
  const cursorsModules = ref(new Map())

  // Debounce-Funktion für Cursor-Updates
  const debounce = (fn, delay) => {
    let timeoutId
    return (...args) => {
      clearTimeout(timeoutId)
      timeoutId = setTimeout(() => fn(...args), delay)
    }
  }

  // Cursor-Positionen aktualisieren
  const handleSelectionChange = (blockId) => {
    const debouncedEmit = debounce((range) => {
      if (socket.value?.connected) {
        socket.value.emit('cursor_update', {
          room: roomId.value,
          blockId,
          range: range
            ? {
                index: range.index,
                length: range.length
              }
            : null
        })
      }
    }, 50)

    return (range, oldRange, source) => {
      if (source === 'user') {
        if (!range) {
          // Entferne Cursor, wenn der Benutzer keinen Bereich mehr ausgewählt hat
          const cursorsModule = cursorsModules.value.get(blockId)
          if (cursorsModule) {
            cursorsModule.removeCursor(socket.value.id)
          }
        }
        debouncedEmit(range)
      }
    }
  }

  // Hebt alle Vorkommen von {{complete_email_history}} hervor
  const createHighlightFunction = (editor) => {
    let inPlaceholderHighlight = false

    return function highlightPlaceholders() {
      if (inPlaceholderHighlight) return
      inPlaceholderHighlight = true
      try {
        const placeholder = '{{complete_email_history}}'
        // Entferne alte Hervorhebungen
        editor.formatText(0, editor.getLength(), 'placeholder', false, Quill.sources.API)
        const text = editor.getText()
        let idx = text.indexOf(placeholder)
        while (idx !== -1) {
          editor.formatText(idx, placeholder.length, 'placeholder', true, Quill.sources.API)
          idx = text.indexOf(placeholder, idx + placeholder.length)
        }
      } finally {
        inPlaceholderHighlight = false
      }
    }
  }

  // Editor für einen Block initialisieren
  const initializeEditor = async (block) => {
    await nextTick()

    const editorElement = editorsMap.value.get(block.id)
    if (!editorElement || editors.value.has(block.id)) {
      return
    }

    const blocksMap = ydoc.value.getMap('blocks')
    const blockMap = blocksMap.get(block.id)
    if (!blockMap) {
      console.error('Block map not found:', block.id)
      return
    }

    let ytext = blockMap.get('content')
    if (!ytext) {
      ytext = new Y.Text()
      blockMap.set('content', ytext)

      // Wenn ein neuer ytext erstellt wurde, sofort synchronisieren
      const update = Y.encodeStateAsUpdate(ydoc.value)
      if (socket.value?.connected) {
        socket.value.emit('sync_update', {
          room: roomId.value,
          update: Array.from(update)
        })
      }
    }

    // Quill Editor mit angepassten Cursor-Einstellungen
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
    })

    const highlightPlaceholders = createHighlightFunction(editor)

    // Hervorhebung nach Yjs-Updates (inkl. lokaler Nutzereingabe)
    ytext.observe(() => {
      setTimeout(() => highlightPlaceholders(), 0)
    })

    // Speichere Referenz zum Cursors Module
    const cursorsModule = editor.getModule('cursors')
    cursorsModules.value.set(block.id, cursorsModule)

    // Binding zwischen Yjs und Quill
    const binding = new QuillBinding(ytext, editor, null, {
      preserveCursor: true
    })

    // Initiale Hervorhebung nach Laden des Inhalts
    highlightPlaceholders()

    // Selection-Change-Handler
    editor.on('selection-change', handleSelectionChange(block.id))

    // NOTE: We no longer broadcast here - autoSync in useYjsCollaboration handles it!
    // QuillBinding syncs Quill <-> Yjs automatically, and ydoc.on('update') in
    // useYjsCollaboration broadcasts incremental updates to other clients.
    // Sending the full state via Y.encodeStateAsUpdate() caused text duplication bugs.

    editors.value.set(block.id, editor)
    bindings.value.set(block.id, binding)
  }

  // Speichert die Editor-Referenz
  const setEditorRef = (el, blockId) => {
    if (el) {
      editorsMap.value.set(blockId, el)
    }
  }

  // Cursor aktualisieren (von anderen Usern)
  const updateCursor = (userId, cursor) => {
    // 1) Wenn cursor === null, entfernen wir den Cursor in allen Blöcken
    if (!cursor) {
      cursorsModules.value.forEach((cursorsModule) => {
        cursorsModule.removeCursor(userId)
      })
      return
    }

    // 2) Wenn range === null, nur den Cursor in dem spezifischen Block entfernen
    const { blockId, range, username, color } = cursor
    const cursorsModule = cursorsModules.value.get(blockId)
    const editor = editors.value.get(blockId)

    if (!range) {
      if (cursorsModule) {
        cursorsModule.removeCursor(userId)
      }
      return
    }

    // 3) Falls es eine gültige Range gibt => Cursor aktualisieren
    if (cursorsModule && editor) {
      if (!cursorsModule.cursors().find(c => c.id === userId)) {
        cursorsModule.createCursor(userId, username, color)
      }

      const transformedRange = editor.getLength() < range.index
        ? { index: editor.getLength(), length: 0 }
        : range

      cursorsModule.moveCursor(userId, transformedRange)
    }
  }

  // Cleanup für gelöschte Blöcke
  const cleanupEditor = (blockId) => {
    const binding = bindings.value.get(blockId)
    if (binding) {
      binding.destroy()
      bindings.value.delete(blockId)
    }

    editors.value.delete(blockId)
    editorsMap.value.delete(blockId)
    cursorsModules.value.delete(blockId)
  }

  // Cleanup aller Editoren
  const cleanupAll = () => {
    bindings.value.forEach(binding => binding.destroy())
    editorsMap.value.clear()
    editors.value.clear()
    bindings.value.clear()
    cursorsModules.value.clear()
  }

  // Placeholder-Highlighting für alle Editoren anwenden
  const applyHighlightingToAll = () => {
    setTimeout(() => {
      editors.value.forEach(editor => {
        if (editor) {
          const text = editor.getText()
          const placeholder = '{{complete_email_history}}'
          let idx = text.indexOf(placeholder)
          while (idx !== -1) {
            editor.formatText(idx, placeholder.length, 'placeholder', true, Quill.sources.API)
            idx = text.indexOf(placeholder, idx + placeholder.length)
          }
        }
      })
    }, 100)
  }

  // Cursor für User entfernen (z.B. wenn User den Raum verlässt)
  const removeCursorForUser = (userId) => {
    cursorsModules.value.forEach(cursorsModule => {
      cursorsModule.removeCursor(userId)
    })
  }

  return {
    editorsMap,
    editors,
    bindings,
    cursorsModules,
    initializeEditor,
    setEditorRef,
    updateCursor,
    cleanupEditor,
    cleanupAll,
    applyHighlightingToAll,
    removeCursorForUser
  }
}
