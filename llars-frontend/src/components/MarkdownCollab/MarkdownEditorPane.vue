<template>
  <div class="editor-pane">
    <div class="editor-topbar">
      <div class="d-flex align-center">
        <v-chip v-if="readonly" size="small" color="warning" variant="tonal" class="mr-2">
          <v-icon start size="small">mdi-lock</v-icon>
          Read-only
        </v-chip>
        <v-chip v-else-if="isConnected" size="small" color="success" variant="tonal" class="mr-2">
          <v-icon start size="small">mdi-cloud-check-outline</v-icon>
          Live Sync
        </v-chip>
        <v-chip v-else size="small" color="warning" variant="tonal" class="mr-2">
          <v-icon start size="small">mdi-cloud-alert-outline</v-icon>
          Reconnecting…
        </v-chip>
      </div>
      <v-spacer />
      <div class="d-flex align-center ga-2 users">
        <v-chip
          v-for="u in activeUsers"
          :key="u.userId"
          size="small"
          variant="tonal"
          :style="{ borderColor: u.color }"
          class="user-chip"
        >
          <span class="user-dot" :style="{ backgroundColor: u.color }" />
          {{ u.username }}
        </v-chip>
      </div>
    </div>

    <div v-if="error" class="px-3 pb-3">
      <v-alert type="error" variant="tonal">
        {{ error }}
      </v-alert>
    </div>

    <v-textarea
      v-if="fallbackMode"
      v-model="fallbackText"
      class="editor-surface"
      :readonly="readonly"
      variant="outlined"
      density="comfortable"
      auto-grow
      hide-details
      @update:modelValue="onFallbackInput"
    />
    <div v-else ref="editorEl" class="editor-surface" />
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as Y from 'yjs'
import { EditorState, StateEffect, StateField, RangeSet } from '@codemirror/state'
import { EditorView, Decoration, WidgetType, highlightActiveLine, drawSelection, highlightSpecialChars, lineNumbers, keymap, gutter, GutterMarker } from '@codemirror/view'
import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands'
import { markdown } from '@codemirror/lang-markdown'
import { defaultHighlightStyle, syntaxHighlighting } from '@codemirror/language'

import { useAuth } from '@/composables/useAuth'
import { useYjsCollaboration } from '@/components/PromptEngineering/composables/useYjsCollaboration'
import { useGitDiff } from './composables/useGitDiff'

const props = defineProps({
  document: { type: Object, required: true },
  readonly: { type: Boolean, default: false }
})

const emit = defineEmits(['content-change', 'git-summary'])

const editorEl = ref(null)
const error = ref('')
const fallbackMode = ref(false)
const fallbackText = ref('')

const view = ref(null)
let ytext = null
let yhighlights = null

const isConnected = ref(false)
const remoteCursors = ref({})
let cursorSendTimer = null

const { tokenParsed, collabColor } = useAuth()
const username = computed(() => tokenParsed.value?.preferred_username || localStorage.getItem('username') || 'user')

const roomId = computed(() => props.document?.yjs_doc_id || `markdown_${props.document?.id}`)

// Git diff for character-level change highlighting
const {
  gitBaseline,
  loadBaseline,
  computeCharacterDiffs,
  diffsToDecorations,
  hasChanges,
  getChangeSummary,
  updateBaseline
} = useGitDiff()

// Track deleted lines for gutter markers
const deletedLinesRef = ref(new Set())

const activeUsers = computed(() => {
  const list = []
  for (const [userId, u] of Object.entries(users.value || {})) {
    list.push({ userId, username: u.username, color: u.color })
  }
  return list
})

// Decorations (git highlights + remote cursors)
const setDecorations = StateEffect.define()
const decorationsField = StateField.define({
  create() {
    return Decoration.none
  },
  update(deco, tr) {
    let next = deco.map(tr.changes)
    for (const e of tr.effects) {
      if (e.is(setDecorations)) next = e.value
    }
    return next
  },
  provide: f => EditorView.decorations.from(f)
})

class CaretWidget extends WidgetType {
  constructor(color, label) {
    super()
    this.color = color
    this.label = label
  }
  toDOM() {
    const wrap = document.createElement('span')
    wrap.className = 'remote-caret'
    wrap.style.borderLeftColor = this.color
    wrap.title = this.label || ''
    return wrap
  }
}

// Gutter marker for deleted lines (red indicator)
class DeletionMarker extends GutterMarker {
  toDOM() {
    const el = document.createElement('div')
    el.className = 'cm-diff-delete-gutter'
    el.title = 'Gelöschter Text'
    return el
  }
}
const deletionMarkerInstance = new DeletionMarker()

let applyingYjsToEditor = false
let skipNextTextSync = false
let applyingDecorations = false

function clampPos(pos, max) {
  if (typeof pos !== 'number' || Number.isNaN(pos)) return 0
  return Math.max(0, Math.min(pos, max))
}

function rgbaFromHex(hex, alpha = 0.18) {
  if (!hex || typeof hex !== 'string') return `rgba(0,0,0,${alpha})`
  const raw = hex.replace('#', '')
  if (raw.length !== 6) return `rgba(0,0,0,${alpha})`
  const r = parseInt(raw.slice(0, 2), 16)
  const g = parseInt(raw.slice(2, 4), 16)
  const b = parseInt(raw.slice(4, 6), 16)
  return `rgba(${r},${g},${b},${alpha})`
}

function updateDecorations() {
  if (!view.value) return
  if (applyingDecorations) return
  const decorations = []

  // Character-level git diff highlighting with user colors
  const currentContent = view.value.state.doc.toString()
  const diffs = computeCharacterDiffs(currentContent)

  if (diffs.length > 0) {
    // Convert Yjs Map to plain object for color lookup
    const highlightsData = {}
    if (yhighlights) {
      try {
        yhighlights.forEach((value, key) => {
          highlightsData[key] = value
        })
      } catch {
        // yhighlights might not be iterable yet
      }
    }

    // Pass highlights data to get user colors for each insertion
    const { decorations: diffDecos, deletedLines } = diffsToDecorations(diffs, view.value, highlightsData)
    decorations.push(...diffDecos)
    deletedLinesRef.value = deletedLines
  } else {
    deletedLinesRef.value = new Set()
  }

  // Remote cursors / selections
  const docLen = view.value.state.doc.length
  for (const [userId, cursor] of Object.entries(remoteCursors.value || {})) {
    if (!cursor || cursor.blockId != String(props.document.id) || !cursor.range) continue
    const color = cursor.color || '#FF6B6B'

    // Decode relative positions if available (prevents cursor drift on remote edits)
    let from, to
    if (cursor.range.fromRel && cursor.range.toRel && ytext && ydoc.value) {
      try {
        const fromRelPos = Y.decodeRelativePosition(new Uint8Array(cursor.range.fromRel))
        const toRelPos = Y.decodeRelativePosition(new Uint8Array(cursor.range.toRel))

        const fromAbsPos = Y.createAbsolutePositionFromRelativePosition(fromRelPos, ydoc.value)
        const toAbsPos = Y.createAbsolutePositionFromRelativePosition(toRelPos, ydoc.value)

        from = fromAbsPos?.index ?? cursor.range.from
        to = toAbsPos?.index ?? cursor.range.to
      } catch {
        // Fallback to absolute positions
        from = cursor.range.from
        to = cursor.range.to
      }
    } else {
      // Use absolute positions (backwards compatibility)
      from = cursor.range.from
      to = cursor.range.to
    }

    from = clampPos(from, docLen)
    to = clampPos(to, docLen)

    if (from !== to) {
      decorations.push(
        Decoration.mark({
          attributes: { style: `background:${rgbaFromHex(color, 0.12)}; border-radius:4px;` }
        }).range(Math.min(from, to), Math.max(from, to))
      )
    }
    decorations.push(
      Decoration.widget({
        widget: new CaretWidget(color, cursor.username),
        side: 1
      }).range(to)
    )
  }

  const decoSet = Decoration.set(decorations, true)
  applyingDecorations = true
  try {
    view.value.dispatch({ effects: setDecorations.of(decoSet) })
  } finally {
    applyingDecorations = false
  }

  // Emit git summary based on actual diffs
  const summary = getChangeSummary(diffs)
  emit('git-summary', {
    users: [], // Could track per-user changes if needed
    totalChangedLines: summary.changes > 0 ? Math.ceil(summary.changes / 40) : 0, // Approximate line count
    insertions: summary.insertions,
    deletions: summary.deletions,
    hasChanges: hasChanges(currentContent)
  })
}

function computeGitSummary() {
  if (!yhighlights) return { users: [], totalChangedLines: 0 }
  const byUser = new Map()
  let total = 0
  for (const [, meta] of yhighlights.entries()) {
    const u = meta?.username || 'unknown'
    const color = meta?.color || '#4ECDC4'
    total += 1
    const cur = byUser.get(u) || { username: u, color, changedLines: 0 }
    cur.changedLines += 1
    byUser.set(u, cur)
  }
  return { users: Array.from(byUser.values()).sort((a, b) => b.changedLines - a.changedLines), totalChangedLines: total }
}

function syncEditorFromYjs() {
  if (!ytext) return
  const text = ytext.toString()
  emit('content-change', text)

  if (fallbackMode.value || !view.value) {
    fallbackText.value = text
    emit('git-summary', computeGitSummary())
    return
  }

  if (skipNextTextSync) {
    skipNextTextSync = false
    return
  }

  if (text === view.value.state.doc.toString()) {
    updateDecorations()
    return
  }

  applyingYjsToEditor = true
  try {
    const sel = view.value.state.selection.main
    view.value.dispatch({
      changes: { from: 0, to: view.value.state.doc.length, insert: text },
      selection: {
        anchor: clampPos(sel.anchor, text.length),
        head: clampPos(sel.head, text.length)
      }
    })
  } finally {
    applyingYjsToEditor = false
    updateDecorations()
  }
}

function updateLocalHighlights(cmUpdate) {
  if (!yhighlights) return
  const changedLines = new Set()
  cmUpdate.changes.iterChanges((fromA, toA, fromB, toB) => {
    const startLine = cmUpdate.state.doc.lineAt(fromB).number
    const endLine = cmUpdate.state.doc.lineAt(toB).number
    for (let ln = startLine; ln <= endLine; ln += 1) changedLines.add(ln)
  })

  // Use persisted collab color from auth, fallback to socket-assigned color
  const userColor = collabColor.value || users.value?.[socket.value?.id]?.color || '#4ECDC4'

  for (const ln of changedLines) {
    yhighlights.set(String(ln), { username: username.value, color: userColor, ts: Date.now() })
  }
}

function sendCursorUpdate(rangeOrNull) {
  if (!socket.value?.connected) return
  socket.value.emit('cursor_update', {
    room: roomId.value,
    blockId: String(props.document.id),
    range: rangeOrNull
  })
}

function scheduleCursorUpdate() {
  if (!view.value || props.readonly || !ytext) return
  if (cursorSendTimer) clearTimeout(cursorSendTimer)
  cursorSendTimer = setTimeout(() => {
    const sel = view.value?.state?.selection?.main
    if (!sel) return

    // Use Y.RelativePosition to handle cursor positions correctly across remote edits
    // This ensures cursors don't shift when text is inserted before them
    try {
      const fromRelPos = Y.createRelativePositionFromTypeIndex(ytext, sel.from)
      const toRelPos = Y.createRelativePositionFromTypeIndex(ytext, sel.to)

      // Encode relative positions for transmission
      const fromEncoded = Array.from(Y.encodeRelativePosition(fromRelPos))
      const toEncoded = Array.from(Y.encodeRelativePosition(toRelPos))

      sendCursorUpdate({
        fromRel: fromEncoded,
        toRel: toEncoded,
        // Keep absolute positions as fallback for backwards compatibility
        from: sel.from,
        to: sel.to
      })
    } catch {
      // Fallback to absolute positions if relative position creation fails
      sendCursorUpdate({ from: sel.from, to: sel.to })
    }
  }, 50)
}

function initEditorIfNeeded() {
  if (!editorEl.value || view.value || !ytext || fallbackMode.value) return

  try {
    const theme = EditorView.theme({
      '&': {
        height: '100%',
        backgroundColor: 'rgb(var(--v-theme-surface))',
        color: 'rgb(var(--v-theme-on-surface))',
        borderRadius: '10px',
        border: '1px solid rgba(var(--v-theme-on-surface), 0.08)'
      },
      '.cm-content': {
        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
        fontSize: '13px'
      },
      '.cm-gutters': {
        backgroundColor: 'transparent',
        borderRight: '1px solid rgba(var(--v-theme-on-surface), 0.08)',
        color: 'rgba(var(--v-theme-on-surface), 0.55)'
      },
      '.cm-activeLineGutter': {
        backgroundColor: 'rgba(var(--v-theme-primary), 0.10)'
      },
      '.cm-activeLine': {
        backgroundColor: 'rgba(var(--v-theme-primary), 0.06)'
      }
    }, { dark: false })

    // Gutter for showing deleted lines (red markers)
    const diffGutter = gutter({
      class: 'cm-diff-gutter',
      markers: (view) => {
        const markers = []
        for (const lineNo of deletedLinesRef.value) {
          if (lineNo >= 1 && lineNo <= view.state.doc.lines) {
            const line = view.state.doc.line(lineNo)
            markers.push(deletionMarkerInstance.range(line.from))
          }
        }
        return RangeSet.of(markers, true)
      }
    })

    const extensions = [
      diffGutter,
      lineNumbers(),
      highlightSpecialChars(),
      drawSelection(),
      highlightActiveLine(),
      history(),
      keymap.of([...defaultKeymap, ...historyKeymap, indentWithTab]),
      markdown(),
      syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
      EditorView.lineWrapping,
      decorationsField,
      theme
    ]

    if (props.readonly) {
      extensions.push(EditorState.readOnly.of(true))
      extensions.push(EditorView.editable.of(false))
    }

    const state = EditorState.create({
      doc: ytext.toString(),
      extensions: [
        ...extensions,
        EditorView.updateListener.of((update) => {
          if (applyingDecorations) return
          if (applyingYjsToEditor) return

          if (update.selectionSet) scheduleCursorUpdate()

          if (!update.docChanged || props.readonly) {
            updateDecorations()
            return
          }

          // Apply CM changes to Yjs text and update git highlights in one transaction
          const changes = []
          update.changes.iterChanges((fromA, toA, _fromB, _toB, inserted) => {
            changes.push({ from: fromA, to: toA, insert: inserted.toString() })
          })

          skipNextTextSync = true
          ydoc.value.transact(() => {
            // Apply in reverse order to keep positions stable
            changes.sort((a, b) => b.from - a.from)
            for (const ch of changes) {
              const delLen = ch.to - ch.from
              if (delLen > 0) ytext.delete(ch.from, delLen)
              if (ch.insert) ytext.insert(ch.from, ch.insert)
            }
            updateLocalHighlights(update)
          }, 'cm')

          emit('content-change', update.state.doc.toString())
          updateDecorations()
        })
      ]
    })

    view.value = new EditorView({ state, parent: editorEl.value })
    nextTick(() => view.value?.focus())
  } catch (e) {
    console.error('CodeMirror init failed:', e)
    error.value = `Editor-Initialisierung fehlgeschlagen: ${e?.message || String(e)}`
    fallbackMode.value = true
    fallbackText.value = ytext?.toString?.() || ''
  }
}

function processYDoc() {
  if (!ydoc.value) return
  ytext = ydoc.value.getText('content')
  yhighlights = ydoc.value.getMap('highlights')
  fallbackText.value = ytext.toString()
  initEditorIfNeeded()
  syncEditorFromYjs()
}

function onUpdateCursor(userId, cursor) {
  const next = { ...(remoteCursors.value || {}) }
  if (!cursor) delete next[userId]
  else next[userId] = cursor
  remoteCursors.value = next
  updateDecorations()
}

function clearHighlights() {
  if (!yhighlights || !ydoc.value) return
  ydoc.value.transact(() => {
    yhighlights.clear()
  }, 'git')
  updateDecorations()
}

/**
 * Refresh the git baseline after a commit
 * This will update the baseline and recalculate all decorations
 */
async function refreshBaseline() {
  await loadBaseline(props.document.id)
  updateDecorations()
}

/**
 * Get current content for commit
 */
function getCurrentContent() {
  if (view.value) {
    return view.value.state.doc.toString()
  }
  if (ytext) {
    return ytext.toString()
  }
  return fallbackText.value || ''
}

function refresh() {
  view.value?.requestMeasure?.()
}

defineExpose({ clearHighlights, refresh, refreshBaseline, getCurrentContent })

const collaboration = useYjsCollaboration(roomId, username.value, processYDoc, onUpdateCursor, { autoSync: true })
const { ydoc, socket, users } = collaboration

let onSocketConnect = null
let onSocketDisconnect = null
let onSocketConnectError = null

onMounted(async () => {
  error.value = ''
  try {
    // Load git baseline for diff comparison
    await loadBaseline(props.document.id)

    collaboration.initialize()
    await nextTick()
    processYDoc()

    // Update decorations after baseline is loaded
    await nextTick()
    updateDecorations()

    const sock = socket.value
    isConnected.value = sock?.connected === true

    onSocketConnect = () => {
      isConnected.value = true
      error.value = ''
    }
    onSocketConnectError = (err) => {
      isConnected.value = false
      const msg = err?.message || err
      error.value = `Collab-Verbindung fehlgeschlagen: ${msg}`
    }
    onSocketDisconnect = () => {
      isConnected.value = false
      if (!props.readonly) error.value = 'Collab-Verbindung getrennt (Reconnecting …)'
    }

    sock?.on('connect', onSocketConnect)
    sock?.on('connect_error', onSocketConnectError)
    sock?.on('disconnect', onSocketDisconnect)
  } catch (e) {
    error.value = e?.message || String(e)
  }
})

watch(
  () => props.readonly,
  () => {
    // Recreate editor on mode change (small component; keeps logic simple)
    view.value?.destroy()
    view.value = null
    initEditorIfNeeded()
  }
)

function onFallbackInput(val) {
  if (props.readonly) return
  if (!ydoc.value || !ytext) return
  const nextText = String(val ?? '')
  const current = ytext.toString()
  if (nextText === current) return

  ydoc.value.transact(() => {
    ytext.delete(0, current.length)
    if (nextText) ytext.insert(0, nextText)
  }, 'fallback')

  emit('content-change', nextText)
  emit('git-summary', computeGitSummary())
}

onUnmounted(() => {
  try {
    sendCursorUpdate(null)
  } catch {}

  if (cursorSendTimer) clearTimeout(cursorSendTimer)
  if (socket.value) {
    if (onSocketConnect) socket.value.off('connect', onSocketConnect)
    if (onSocketConnectError) socket.value.off('connect_error', onSocketConnectError)
    if (onSocketDisconnect) socket.value.off('disconnect', onSocketDisconnect)
  }
  view.value?.destroy()
  view.value = null
  collaboration.cleanup()
})
</script>

<style scoped>
.editor-pane {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.editor-topbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.editor-surface {
  flex: 1;
  min-height: 240px;
}

.users {
  flex-wrap: wrap;
  justify-content: flex-end;
  max-width: 60%;
}

.user-chip {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}

.user-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 6px;
}

:global(.remote-caret) {
  border-left: 2px solid;
  margin-left: -1px;
  height: 1.2em;
  display: inline-block;
}

/* Git diff highlighting - character level with underline */
:global(.cm-diff-insert) {
  background: rgba(72, 187, 120, 0.35) !important;
  border-radius: 2px;
  box-shadow: 0 0 0 1px rgba(72, 187, 120, 0.5);
  text-decoration: underline;
  text-decoration-color: rgba(72, 187, 120, 0.8);
  text-underline-offset: 2px;
}

/* Diff gutter styling */
:global(.cm-diff-gutter) {
  width: 4px;
  min-width: 4px;
  margin-right: 2px;
}

:global(.cm-diff-delete-gutter) {
  width: 4px;
  height: 100%;
  background: rgba(245, 101, 101, 0.8);
  border-radius: 1px;
}

/* Real-time user edit line highlighting */
:global(.cm-user-edit-line) {
  transition: background-color 0.3s ease, border-color 0.3s ease;
}
</style>
