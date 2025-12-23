import { ref, nextTick, markRaw } from 'vue'
import Quill from 'quill'
import { QuillBinding } from 'y-quill'
import * as Y from 'yjs'

export function useQuillEditor(ydoc, socket, roomId, options = {}) {
  const editorsMap = new Map()
  const editors = new Map()
  const bindings = new Map()
  const cursorsModules = new Map()
  const ytexts = new Map()
  const initializingEditors = new Set()
  const editorCount = ref(0)

  // User highlighting options
  const { getUserColor = () => null, getUsername = () => null } = options

  // Track user highlights per block
  const userHighlights = new Map() // blockId -> Map<position, {username, color, ts}>
  const pendingHighlights = new Map() // blockId -> Array<{ index, length }>

  // Debounce-Funktion für Cursor-Updates
  const debounce = (fn, delay) => {
    let timeoutId
    return (...args) => {
      clearTimeout(timeoutId)
      timeoutId = setTimeout(() => fn(...args), delay)
    }
  }

  const cursorEmitters = new Map()

  const buildCursorPayload = (blockId, range) => {
    if (!range) return null

    const payload = {
      index: range.index,
      length: range.length
    }

    const ytext = ytexts.get(blockId)
    if (!ytext) return payload

    try {
      const fromRel = Y.createRelativePositionFromTypeIndex(ytext, range.index)
      const toRel = Y.createRelativePositionFromTypeIndex(ytext, range.index + range.length)
      payload.fromRel = Array.from(Y.encodeRelativePosition(fromRel))
      payload.toRel = Array.from(Y.encodeRelativePosition(toRel))
    } catch (e) {
      // Ignore encoding errors and fallback to absolute positions
    }

    return payload
  }

  const emitCursorUpdate = (blockId, range) => {
    if (!cursorEmitters.has(blockId)) {
      cursorEmitters.set(blockId, debounce((payload) => {
        if (socket.value?.connected) {
          socket.value.emit('cursor_update', {
            room: roomId.value,
            blockId,
            range: payload
          })
        }
      }, 50))
    }

    const payload = buildCursorPayload(blockId, range)
    cursorEmitters.get(blockId)(payload)
  }

  // Cursor-Positionen aktualisieren
  const handleSelectionChange = (blockId) => {
    return (range, oldRange, source) => {
      if (source === 'user') {
        if (!range) {
          // Entferne Cursor, wenn der Benutzer keinen Bereich mehr ausgewählt hat
          const cursorsModule = cursorsModules.get(blockId)
          if (cursorsModule) {
            cursorsModule.removeCursor(socket.value.id)
          }
        }
        emitCursorUpdate(blockId, range)
      }
    }
  }

  // Helper: Convert hex to rgba
  const hexToRgba = (hex, alpha = 0.25) => {
    if (!hex || typeof hex !== 'string') return `rgba(0,0,0,${alpha})`
    const raw = hex.replace('#', '')
    if (raw.length !== 6) return `rgba(0,0,0,${alpha})`
    const r = parseInt(raw.slice(0, 2), 16)
    const g = parseInt(raw.slice(2, 4), 16)
    const b = parseInt(raw.slice(4, 6), 16)
    return `rgba(${r},${g},${b},${alpha})`
  }

  // Apply user highlighting to inserted text
  const queuePendingHighlight = (blockId, index, length) => {
    if (!pendingHighlights.has(blockId)) {
      pendingHighlights.set(blockId, [])
    }
    pendingHighlights.get(blockId).push({ index, length })
  }

  const flushPendingHighlights = () => {
    const color = getUserColor()
    if (!color) return
    const highlightColor = hexToRgba(color, 0.3)

    pendingHighlights.forEach((ranges, blockId) => {
      const editor = editors.get(blockId)
      if (!editor) return
      ranges.forEach(({ index, length }) => {
        try {
          editor.formatText(index, length, {
            'llars-user-highlight': highlightColor
          }, Quill.sources.API)
        } catch (e) {
          // Ignore formatting errors
        }
      })
    })

    pendingHighlights.clear()
  }

  const applyUserHighlight = (editor, blockId, delta, source) => {
    if (source !== 'user') return

    const username = getUsername()
    if (!username) return

    const color = getUserColor()
    if (color) {
      flushPendingHighlights()
    }

    let position = 0
    const highlights = userHighlights.get(blockId) || new Map()

    delta.ops.forEach(op => {
      if (op.retain) {
        position += op.retain
      } else if (op.insert && typeof op.insert === 'string') {
        // Track this insertion
        const insertLength = op.insert.length
        for (let i = 0; i < insertLength; i++) {
          highlights.set(position + i, { username, color, ts: Date.now() })
        }

        // Apply user highlight formatting
        const startIndex = position
        const length = insertLength
        setTimeout(() => {
          try {
            const resolvedColor = getUserColor()
            if (!resolvedColor) {
              queuePendingHighlight(blockId, startIndex, length)
              return
            }
            editor.formatText(startIndex, length, {
              'llars-user-highlight': hexToRgba(resolvedColor, 0.3)
            }, Quill.sources.API)
          } catch (e) {
            // Ignore formatting errors
          }
        }, 0)

        position += insertLength
      } else if (op.delete) {
        // Remove highlights for deleted positions
        for (let i = 0; i < op.delete; i++) {
          highlights.delete(position + i)
        }
      }
    })

    userHighlights.set(blockId, highlights)
  }

  const highlightFormat = 'highlight'

  const resetEditor = (blockId, options = {}) => {
    const { keepElementRef = true, elementOverride = null } = options
    const editor = editors.get(blockId) || null
    const editorElement = elementOverride || editorsMap.get(blockId) || editor?.container || null

    const bindingCandidates = [
      bindings.get(blockId) || null,
      editorElement?.__llarsYjsBinding || null,
      editor?.__llarsYjsBinding || null
    ].filter(Boolean)
    const uniqueBindings = Array.from(new Set(bindingCandidates))

    uniqueBindings.forEach(binding => {
      try {
        binding.destroy()
      } catch (e) {
        // Ignore cleanup errors
      }
    })

    if (editor) {
      try {
        editor.off('selection-change')
        editor.off('text-change')
      } catch (e) {
        // Ignore errors while detaching handlers
      }
      try {
        editor.enable(false)
      } catch (e) {
        // Ignore disable errors
      }
      delete editor.__llarsHandlersAttached
      delete editor.__llarsHighlightAttached
      delete editor.__llarsYjsBinding
    }

    bindings.delete(blockId)
    cursorsModules.delete(blockId)
    ytexts.delete(blockId)
    cursorEmitters.delete(blockId)
    editors.delete(blockId)
    pendingHighlights.delete(blockId)
    editorCount.value = editors.size

    if (editorElement) {
      editorElement.innerHTML = ''
      delete editorElement.__llarsYjsBinding
      delete editorElement.__quill
    }

    if (!keepElementRef) {
      editorsMap.delete(blockId)
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
        editor.formatText(0, editor.getLength(), highlightFormat, false, Quill.sources.API)
        const text = editor.getText()
        let idx = text.indexOf(placeholder)
        while (idx !== -1) {
          editor.formatText(idx, placeholder.length, highlightFormat, true, Quill.sources.API)
          idx = text.indexOf(placeholder, idx + placeholder.length)
        }
      } finally {
        inPlaceholderHighlight = false
      }
    }
  }

  // Editor für einen Block initialisieren
  const initializeEditor = async (block) => {
    let editorElement = editorsMap.get(block.id)
    if (!editorElement) {
      await nextTick()
      editorElement = editorsMap.get(block.id)
    }

    if (!editorElement) {
      return
    }

    if (initializingEditors.has(block.id)) {
      return
    }

    initializingEditors.add(block.id)
    try {
      const mapEditor = editors.get(block.id) || null
      const elementEditor = editorElement.__quill || null
      let existingEditor = null

      if (elementEditor) {
        existingEditor = elementEditor
      } else if (mapEditor && mapEditor.container === editorElement) {
        existingEditor = mapEditor
      }

      const bindingFromMap = bindings.get(block.id) || null
      const bindingFromElement = editorElement.__llarsYjsBinding || null
      const bindingFromEditor = existingEditor?.__llarsYjsBinding || null
      const bindingCandidates = [bindingFromMap, bindingFromElement, bindingFromEditor].filter(Boolean)
      const uniqueBindings = Array.from(new Set(bindingCandidates))
      let existingBinding = null

      if (existingEditor) {
        existingBinding = uniqueBindings.find(binding => binding.quill === existingEditor) || null
      }

      const duplicateEditors = editorElement.querySelectorAll('.ql-editor').length > 1
      const duplicateContainers = editorElement.querySelectorAll('.ql-container').length > 1
      const duplicateToolbars = editorElement.querySelectorAll('.ql-toolbar').length > 1
      const hasDuplicateDom = duplicateEditors || duplicateContainers || duplicateToolbars
      const containerMismatch = existingEditor && existingEditor.container !== editorElement
      const needsReset = hasDuplicateDom || containerMismatch || uniqueBindings.length > 1 || (existingEditor && !existingBinding) || (!existingEditor && uniqueBindings.length > 0)

      if (needsReset) {
        resetEditor(block.id, { keepElementRef: true, elementOverride: editorElement })
        existingEditor = null
        existingBinding = null
      }

      const canReuseBinding = existingEditor && existingBinding && existingBinding.quill === existingEditor

      if (canReuseBinding) {
        const rawEditor = markRaw(existingEditor)
        const rawBinding = markRaw(existingBinding)
        editors.set(block.id, rawEditor)
        bindings.set(block.id, rawBinding)
        const cursorsModule = rawEditor.getModule('cursors')
        if (cursorsModule) {
          cursorsModules.set(block.id, markRaw(cursorsModule))
        }
        editorElement.__llarsYjsBinding = rawBinding
        rawEditor.__llarsYjsBinding = rawBinding
        rawEditor.enable(true)
        editorCount.value = editors.size
        return
      }

      if (!ydoc.value) {
        console.error('Y.Doc not initialized for block:', block.id)
        return
      }

      const blocksMap = ydoc.value.getMap('blocks')
      const blockMap = blocksMap.get(block.id)
      if (!blockMap) {
        console.error('Block map not found:', block.id)
        return
      }

      let ytext = blockMap.get('content')
      if (!(ytext instanceof Y.Text)) {
        const seed = typeof ytext === 'string' ? ytext : ''
        ytext = new Y.Text()
        if (seed) {
          ytext.insert(0, seed)
        }
        blockMap.set('content', ytext)
        // NOTE: autoSync in useYjsCollaboration handles broadcasting automatically
      }
      ytexts.set(block.id, ytext)

      // Quill Editor mit angepassten Cursor-Einstellungen
      const editor = markRaw(existingEditor || new Quill(editorElement, {
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
      }))

      const highlightPlaceholders = createHighlightFunction(editor)

      if (!editor.__llarsHighlightAttached) {
        editor.__llarsHighlightAttached = true
        // Hervorhebung nach Yjs-Updates (inkl. lokaler Nutzereingabe)
        ytext.observe(() => {
          setTimeout(() => highlightPlaceholders(), 0)
        })
      }

      // Speichere Referenz zum Cursors Module
      const cursorsModule = editor.getModule('cursors')
      if (cursorsModule) {
        cursorsModules.set(block.id, markRaw(cursorsModule))
      }

      // Binding zwischen Yjs und Quill
      const binding = markRaw(existingBinding || new QuillBinding(ytext, editor, null, {
        preserveCursor: true
      }))
      editorElement.__llarsYjsBinding = binding
      editor.__llarsYjsBinding = binding

      // Initiale Hervorhebung nach Laden des Inhalts
      highlightPlaceholders()

      if (!editor.__llarsHandlersAttached) {
        editor.__llarsHandlersAttached = true
        // Selection-Change-Handler
        editor.on('selection-change', handleSelectionChange(block.id))

        // Text-Change-Handler for user highlighting + cursor updates
        editor.on('text-change', (delta, oldDelta, source) => {
          applyUserHighlight(editor, block.id, delta, source)
          if (source === 'user') {
            emitCursorUpdate(block.id, editor.getSelection())
          }
        })
      }

      // NOTE: We no longer broadcast here - autoSync in useYjsCollaboration handles it!
      // QuillBinding syncs Quill <-> Yjs automatically, and ydoc.on('update') in
      // useYjsCollaboration broadcasts incremental updates to other clients.
      // Sending the full state via Y.encodeStateAsUpdate() caused text duplication bugs.

      editor.enable(true)

      editors.set(block.id, editor)
      bindings.set(block.id, binding)
      editorCount.value = editors.size
    } catch (error) {
      console.error('Failed to initialize Quill editor:', error)
    } finally {
      initializingEditors.delete(block.id)
    }
  }

  // Speichert die Editor-Referenz
  const setEditorRef = (el, block) => {
    if (!el || !block?.id) {
      return
    }

    const existingElement = editorsMap.get(block.id)
    if (existingElement && existingElement !== el) {
      resetEditor(block.id, { keepElementRef: false, elementOverride: existingElement })
    }

    editorsMap.set(block.id, el)
    initializeEditor(block)
  }

  // Cursor aktualisieren (von anderen Usern)
  const updateCursor = (userId, cursor) => {
    // 1) Wenn cursor === null, entfernen wir den Cursor in allen Blöcken
    if (!cursor) {
      cursorsModules.forEach((cursorsModule) => {
        cursorsModule.removeCursor(userId)
      })
      return
    }

    // 2) Wenn range === null, nur den Cursor in dem spezifischen Block entfernen
    const { blockId, range, username, color } = cursor
    const cursorsModule = cursorsModules.get(blockId)
    const editor = editors.get(blockId)

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

      const resolveCursorRange = (targetBlockId, rawRange, quillEditor) => {
        if (!rawRange || !quillEditor) return null
        let from = null
        let to = null

        const ytext = ytexts.get(targetBlockId)
        if (ytext && ydoc.value && rawRange.fromRel && rawRange.toRel) {
          try {
            const fromRelPos = Y.decodeRelativePosition(new Uint8Array(rawRange.fromRel))
            const toRelPos = Y.decodeRelativePosition(new Uint8Array(rawRange.toRel))
            const fromAbsPos = Y.createAbsolutePositionFromRelativePosition(fromRelPos, ydoc.value)
            const toAbsPos = Y.createAbsolutePositionFromRelativePosition(toRelPos, ydoc.value)
            from = fromAbsPos?.index ?? null
            to = toAbsPos?.index ?? null
          } catch (e) {
            // Ignore decoding errors and fallback to absolute positions
          }
        }

        if (from === null || to === null) {
          if (typeof rawRange.index === 'number') {
            from = rawRange.index
            const len = typeof rawRange.length === 'number' ? rawRange.length : 0
            to = from + len
          } else if (typeof rawRange.from === 'number' && typeof rawRange.to === 'number') {
            from = rawRange.from
            to = rawRange.to
          } else {
            from = 0
            to = 0
          }
        }

        const maxLen = quillEditor.getLength()
        const clamp = (value) => Math.max(0, Math.min(value ?? 0, maxLen))
        const start = Math.min(clamp(from), clamp(to))
        const end = Math.max(clamp(from), clamp(to))
        return { index: start, length: end - start }
      }

      const resolvedRange = resolveCursorRange(blockId, range, editor)
      if (!resolvedRange) return
      cursorsModule.moveCursor(userId, resolvedRange)
    }
  }

  // Cleanup für gelöschte Blöcke
  const cleanupEditor = (blockId) => {
    initializingEditors.delete(blockId)
    resetEditor(blockId, { keepElementRef: false })
  }

  // Cleanup aller Editoren
  const cleanupAll = () => {
    const blockIds = new Set([
      ...editorsMap.keys(),
      ...editors.keys(),
      ...bindings.keys()
    ])

    blockIds.forEach(blockId => {
      resetEditor(blockId, { keepElementRef: false })
    })

    editorsMap.clear()
    editors.clear()
    bindings.clear()
    cursorsModules.clear()
    ytexts.clear()
    cursorEmitters.clear()
    pendingHighlights.clear()
    editorCount.value = 0
    initializingEditors.clear()
  }

  // Placeholder-Highlighting für alle Editoren anwenden
  const applyHighlightingToAll = () => {
    setTimeout(() => {
      editors.forEach(editor => {
        if (editor) {
          const text = editor.getText()
          const placeholder = '{{complete_email_history}}'
          let idx = text.indexOf(placeholder)
          while (idx !== -1) {
            editor.formatText(idx, placeholder.length, highlightFormat, true, Quill.sources.API)
            idx = text.indexOf(placeholder, idx + placeholder.length)
          }
        }
      })
    }, 100)
  }

  // Cursor für User entfernen (z.B. wenn User den Raum verlässt)
  const removeCursorForUser = (userId) => {
    cursorsModules.forEach(cursorsModule => {
      cursorsModule.removeCursor(userId)
    })
  }

  // Clear all user highlights (e.g., after commit)
  const clearUserHighlights = () => {
    userHighlights.clear()
    pendingHighlights.clear()

    // Remove user highlighting formatting from all editors
    editors.forEach((editor) => {
      try {
        const length = editor.getLength()
        if (length > 0) {
          editor.formatText(0, length, {
            'llars-user-highlight': false,
            'background': false
          }, Quill.sources.API)
        }
      } catch (e) {
        // Ignore errors
      }
    })
  }

  return {
    editorsMap,
    editors,
    bindings,
    cursorsModules,
    userHighlights,
    editorCount,
    initializeEditor,
    setEditorRef,
    updateCursor,
    cleanupEditor,
    cleanupAll,
    applyHighlightingToAll,
    removeCursorForUser,
    clearUserHighlights,
    flushPendingHighlights
  }
}
