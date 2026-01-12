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
  const {
    getUserColor = () => null,
    getUsername = () => null,
    onUserTextChange = null
  } = options

  // Track user highlights per block
  const userHighlights = new Map() // blockId -> Map<position, {username, color, ts}>
  const pendingHighlights = new Map() // blockId -> Array<{ index, length }>
  const remoteCursors = new Map() // userId -> { blockId, range, username, color }

  // Debounce-Funktion für Cursor-Updates
  const debounce = (fn, delay) => {
    let timeoutId
    return (...args) => {
      clearTimeout(timeoutId)
      timeoutId = setTimeout(() => fn(...args), delay)
    }
  }

  const cursorEmitters = new Map()
  const selectionSuppression = new Map()

  const suppressSelectionUpdates = (blockId, duration = 80) => {
    const existingTimeout = selectionSuppression.get(blockId)
    if (existingTimeout) {
      clearTimeout(existingTimeout)
    }
    const timeoutId = setTimeout(() => {
      selectionSuppression.delete(blockId)
    }, duration)
    selectionSuppression.set(blockId, timeoutId)
  }

  const isSelectionSuppressed = (blockId) => selectionSuppression.has(blockId)

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

  const resolveCursorRange = (blockId, rawRange, quillEditor) => {
    if (!rawRange || !quillEditor) return null
    const hasRelativePayload = Boolean(rawRange.fromRel && rawRange.toRel)
    let from = null
    let to = null

    const ytext = ytexts.get(blockId)
    if (ytext && ydoc.value && hasRelativePayload) {
      try {
        const fromRelPos = Y.decodeRelativePosition(new Uint8Array(rawRange.fromRel))
        const toRelPos = Y.decodeRelativePosition(new Uint8Array(rawRange.toRel))
        const fromAbsPos = Y.createAbsolutePositionFromRelativePosition(fromRelPos, ydoc.value)
        const toAbsPos = Y.createAbsolutePositionFromRelativePosition(toRelPos, ydoc.value)
        const hasFrom = typeof fromAbsPos?.index === 'number'
        const hasTo = typeof toAbsPos?.index === 'number'
        if (!hasFrom || !hasTo) {
          return null
        }
        from = fromAbsPos.index
        to = toAbsPos.index
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

  const applyRemoteCursor = (userId, cursor) => {
    if (!cursor) return
    const { blockId, range, username, color } = cursor
    const cursorsModule = cursorsModules.get(blockId)
    const editor = editors.get(blockId)

    if (!range) {
      if (cursorsModule) {
        cursorsModule.removeCursor(userId)
      }
      return
    }

    if (cursorsModule && editor) {
      const resolvedRange = resolveCursorRange(blockId, range, editor)
      if (!resolvedRange) return
      if (!cursorsModule.cursors().find(c => c.id === userId)) {
        cursorsModule.createCursor(userId, username, color)
      }
      cursorsModule.moveCursor(userId, resolvedRange)
    }
  }

  const refreshBlockCursors = (blockId) => {
    remoteCursors.forEach((cursor, userId) => {
      if (cursor?.blockId === blockId) {
        applyRemoteCursor(userId, cursor)
      }
    })
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
          emitCursorUpdate(blockId, range)
          return
        }
        if (isSelectionSuppressed(blockId)) {
          return
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
    const suppressionTimeout = selectionSuppression.get(blockId)
    if (suppressionTimeout) {
      clearTimeout(suppressionTimeout)
      selectionSuppression.delete(blockId)
    }
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

  // Regex für alle {{variablen}} Platzhalter
  const PLACEHOLDER_REGEX = /\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}/g
  const INVALID_VAR_NAMES = new Set(['undefined', 'null', 'true', 'false', 'NaN', 'Infinity'])

  // Konvertiert {{variablen}} Text zu Embed-Blots (atomare Elemente)
  const createHighlightFunction = (editor) => {
    let inPlaceholderConversion = false

    return function convertPlaceholdersToEmbeds() {
      if (inPlaceholderConversion) return
      inPlaceholderConversion = true

      try {
        const text = editor.getText()

        // Finde alle {{variablen}} Platzhalter (von hinten nach vorne, um Indizes nicht zu verschieben)
        const matches = []
        let match
        const regex = new RegExp(PLACEHOLDER_REGEX.source, 'g')
        while ((match = regex.exec(text)) !== null) {
          const varName = match[1]
          // Überspringe ungültige Variablennamen
          if (INVALID_VAR_NAMES.has(varName)) {
            continue
          }
          matches.push({
            index: match.index,
            length: match[0].length,
            varName
          })
        }

        // Konvertiere von hinten nach vorne (um Indizes konsistent zu halten)
        for (let i = matches.length - 1; i >= 0; i--) {
          const m = matches[i]

          // Prüfe, ob an dieser Position bereits ein Embed ist
          const [leaf] = editor.getLeaf(m.index)
          if (leaf && leaf.statics && leaf.statics.blotName === 'variable') {
            continue // Bereits ein Embed-Blot
          }

          // Lösche den Text und füge ein Embed ein
          editor.deleteText(m.index, m.length, Quill.sources.SILENT)
          editor.insertEmbed(m.index, 'variable', m.varName, Quill.sources.SILENT)
        }
      } finally {
        inPlaceholderConversion = false
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
            transformOnTextChange: false,
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
          setTimeout(() => {
            highlightPlaceholders()
            refreshBlockCursors(block.id)
          }, 0)
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
            suppressSelectionUpdates(block.id)
            emitCursorUpdate(block.id, editor.getSelection())
            if (typeof onUserTextChange === 'function') {
              onUserTextChange({ blockId: block.id, delta, editor })
            }
          }
        })

        // Create drop cursor indicator element - positioned outside the contentEditable
        let dropCursor = null

        // Inject animation style once
        if (!document.getElementById('llars-drop-cursor-style')) {
          const style = document.createElement('style')
          style.id = 'llars-drop-cursor-style'
          style.textContent = `
            @keyframes llarsDropCursorBlink {
              0%, 100% { opacity: 1; }
              50% { opacity: 0.3; }
            }
          `
          document.head.appendChild(style)
        }

        const getDropCursor = () => {
          if (!dropCursor) {
            dropCursor = document.createElement('div')
            dropCursor.className = 'ql-drop-cursor'
            dropCursor.setAttribute('contenteditable', 'false')
            dropCursor.style.cssText = `
              position: fixed;
              width: 2px;
              height: 20px;
              background: #88c4c8;
              pointer-events: none;
              z-index: 10000;
              animation: llarsDropCursorBlink 0.8s ease-in-out infinite;
              box-shadow: 0 0 4px rgba(136, 196, 200, 0.8);
              border-radius: 1px;
              display: none;
            `
            // Append to body to avoid contentEditable issues
            document.body.appendChild(dropCursor)
          }
          return dropCursor
        }

        // Update drop cursor position based on mouse coordinates
        const updateDropCursor = (e) => {
          const cursor = getDropCursor()

          if (document.caretRangeFromPoint) {
            const range = document.caretRangeFromPoint(e.clientX, e.clientY)
            if (range && editor.root.contains(range.startContainer)) {
              // Get the bounding rect of the caret position
              const rects = range.getClientRects()
              if (rects.length > 0) {
                const rect = rects[0]

                // Position cursor using fixed positioning (relative to viewport)
                cursor.style.left = `${rect.left}px`
                cursor.style.top = `${rect.top}px`
                cursor.style.height = `${rect.height || 20}px`
                cursor.style.display = 'block'
                return
              }
            }
          }

          // Hide cursor if we can't determine position
          if (cursor) {
            cursor.style.display = 'none'
          }
        }

        const hideDropCursor = () => {
          if (dropCursor) {
            dropCursor.style.display = 'none'
          }
        }

        // Remove any old cursor elements that might have been left in the editor
        const oldCursors = editor.root.querySelectorAll('.ql-drop-cursor')
        oldCursors.forEach(el => el.remove())

        // Placeholder drop handler - allows dragging placeholders from palette or moving within editor
        // Use capture: true to intercept events before Quill can handle them
        editor.root.addEventListener('dragover', (e) => {
          // Only handle variable drags
          const isVariableDrag = window.__llarsVariableDrag || e.dataTransfer.types.includes('text/placeholder')
          if (!isVariableDrag) {
            hideDropCursor()
            return
          }

          e.preventDefault()
          e.stopPropagation()
          // Use 'move' if moving within editor, 'copy' if from palette
          e.dataTransfer.dropEffect = window.__llarsVariableDrag ? 'move' : 'copy'
          editor.root.classList.add('placeholder-drop-target')

          // Update drop cursor position
          updateDropCursor(e)
        }, { capture: true })

        editor.root.addEventListener('dragleave', (e) => {
          // Only remove class if actually leaving the editor (not entering a child)
          if (!editor.root.contains(e.relatedTarget)) {
            editor.root.classList.remove('placeholder-drop-target')
            hideDropCursor()
          }
        }, { capture: true })

        editor.root.addEventListener('drop', (e) => {
          editor.root.classList.remove('placeholder-drop-target')
          hideDropCursor()

          // Check if this is a variable being moved within the editor
          const variableMove = e.dataTransfer.getData('text/variable-move')

          // Check if this is a placeholder drop from the palette
          const placeholderName = e.dataTransfer.getData('text/placeholder')

          if (variableMove || placeholderName) {
            e.preventDefault()
            e.stopPropagation()

            const varName = variableMove || placeholderName

            // Get drop position by finding the character offset at mouse position
            let insertIndex = editor.getLength() - 1

            // Try to get position from mouse coordinates
            if (document.caretRangeFromPoint) {
              const range = document.caretRangeFromPoint(e.clientX, e.clientY)
              if (range && editor.root.contains(range.startContainer)) {
                const blot = Quill.find(range.startContainer, true)
                if (blot) {
                  const blotIndex = editor.getIndex(blot)
                  insertIndex = blotIndex + range.startOffset
                }
              }
            }

            // If moving a variable within the editor, we need to delete the original
            if (variableMove && window.__llarsVariableDrag) {
              const draggedNode = window.__llarsVariableDrag.node
              const quillBlot = Quill.find(draggedNode)

              if (quillBlot && editor.root.contains(draggedNode)) {
                const sourceIndex = editor.getIndex(quillBlot)

                // Adjust insertIndex if removing before insert position
                if (sourceIndex < insertIndex) {
                  insertIndex -= 1
                }

                // Delete the original
                editor.deleteText(sourceIndex, 1, 'silent')
              }

              // Clear the drag state
              window.__llarsVariableDrag = null
            }

            // Insert the variable as an embed blot (atomic element)
            editor.insertEmbed(insertIndex, 'variable', varName, 'user')

            // Move cursor after the inserted embed (length is 1)
            editor.setSelection(insertIndex + 1, 0)
          }
        }, { capture: true })

        // Also add handlers to the container (prevents Quill's default drop behavior)
        // Note: We only preventDefault here, NOT stopPropagation, so the root handler still fires
        editor.container.addEventListener('dragover', (e) => {
          if (window.__llarsVariableDrag || e.dataTransfer.types.includes('text/placeholder')) {
            e.preventDefault()
            e.dataTransfer.dropEffect = window.__llarsVariableDrag ? 'move' : 'copy'
          }
        }, { capture: true })

        // Variable embeds are already draggable by default (set in VariableBlot.create)
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
      remoteCursors.delete(userId)
      cursorsModules.forEach((cursorsModule) => {
        cursorsModule.removeCursor(userId)
      })
      return
    }

    remoteCursors.set(userId, cursor)
    applyRemoteCursor(userId, cursor)
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
    selectionSuppression.forEach(timeoutId => clearTimeout(timeoutId))
    selectionSuppression.clear()
    remoteCursors.clear()
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
          const length = editor.getLength()

          // Entferne alle alten Hervorhebungen
          editor.formatText(0, length, highlightFormat, false, Quill.sources.API)

          // Finde und highlighte ALLE {{variablen}} Platzhalter
          let match
          const regex = new RegExp(PLACEHOLDER_REGEX.source, 'g')
          while ((match = regex.exec(text)) !== null) {
            const varName = match[1]
            // Überspringe ungültige Variablennamen
            if (['undefined', 'null', 'true', 'false', 'NaN', 'Infinity'].includes(varName)) {
              continue
            }
            editor.formatText(match.index, match[0].length, highlightFormat, true, Quill.sources.API)
          }
        }
      })
    }, 100)
  }

  // Cursor für User entfernen (z.B. wenn User den Raum verlässt)
  const removeCursorForUser = (userId) => {
    remoteCursors.delete(userId)
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
