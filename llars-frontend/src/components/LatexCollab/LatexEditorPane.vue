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
import { autocompletion, completionKeymap } from '@codemirror/autocomplete'
import { stex } from '@codemirror/legacy-modes/mode/stex'
import { StreamLanguage, defaultHighlightStyle, syntaxHighlighting } from '@codemirror/language'

import { useAuth } from '@/composables/useAuth'
import { useYjsCollaboration } from '@/components/PromptEngineering/composables/useYjsCollaboration'
import { useGitDiff } from '@/components/MarkdownCollab/composables/useGitDiff'
import { useTypingMetrics } from '@/composables/useAnalyticsMetrics'

const props = defineProps({
  document: { type: Object, required: true },
  readonly: { type: Boolean, default: false },
  comments: { type: Array, default: () => [] },
  activeCommentId: { type: Number, default: null }
})

const emit = defineEmits(['content-change', 'git-summary', 'cursor-change', 'sync-request'])

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
let cursorChangeTimer = null

const { tokenParsed, collabColor } = useAuth()
const username = computed(() => tokenParsed.value?.preferred_username || localStorage.getItem('username') || 'user')

const roomId = computed(() => props.document?.yjs_doc_id || `latex_${props.document?.id}`)

// Analytics: Typing metrics for this document
const documentEntity = computed(() => `doc:${props.document?.id}`)
const typingMetrics = useTypingMetrics({
  category: 'latex',
  name: () => documentEntity.value,
  dimensions: () => ({ entity: documentEntity.value, view: 'editor' })
})

// Git diff for character-level change highlighting
const {
  gitBaseline,
  loadBaseline,
  computeCharacterDiffs,
  diffsToDecorations,
  hasChanges,
  getChangeSummary,
  updateBaseline
} = useGitDiff({ apiPrefix: '/api/latex-collab' })

// Track deleted lines for gutter markers
const deletedLinesRef = ref(new Set())

const latexCommandCompletions = [
  { label: '\\documentclass', type: 'keyword', info: 'Dokumentklasse', apply: '\\documentclass{}' },
  { label: '\\usepackage', type: 'keyword', info: 'Paket laden', apply: '\\usepackage{}' },
  { label: '\\begin', type: 'keyword', info: 'Umgebung starten', apply: '\\begin{}' },
  { label: '\\end', type: 'keyword', info: 'Umgebung beenden', apply: '\\end{}' },
  { label: '\\section', type: 'keyword', info: 'Abschnitt', apply: '\\section{}' },
  { label: '\\subsection', type: 'keyword', info: 'Unterabschnitt', apply: '\\subsection{}' },
  { label: '\\subsubsection', type: 'keyword', info: 'Unter-Unterabschnitt', apply: '\\subsubsection{}' },
  { label: '\\paragraph', type: 'keyword', info: 'Paragraph', apply: '\\paragraph{}' },
  { label: '\\textbf', type: 'function', info: 'Fett', apply: '\\textbf{}' },
  { label: '\\textit', type: 'function', info: 'Kursiv', apply: '\\textit{}' },
  { label: '\\emph', type: 'function', info: 'Hervorheben', apply: '\\emph{}' },
  { label: '\\underline', type: 'function', info: 'Unterstreichen', apply: '\\underline{}' },
  { label: '\\item', type: 'keyword', info: 'Listenpunkt', apply: '\\item ' },
  { label: '\\label', type: 'keyword', info: 'Label', apply: '\\label{}' },
  { label: '\\ref', type: 'keyword', info: 'Referenz', apply: '\\ref{}' },
  { label: '\\pageref', type: 'keyword', info: 'Seitenreferenz', apply: '\\pageref{}' },
  { label: '\\cite', type: 'keyword', info: 'Zitat', apply: '\\cite{}' },
  { label: '\\citet', type: 'keyword', info: 'Textzitat', apply: '\\citet{}' },
  { label: '\\citep', type: 'keyword', info: 'Klammerzitat', apply: '\\citep{}' },
  { label: '\\includegraphics', type: 'keyword', info: 'Grafik', apply: '\\includegraphics[]{}' },
  { label: '\\caption', type: 'keyword', info: 'Caption', apply: '\\caption{}' },
  { label: '\\centering', type: 'keyword', info: 'Zentrieren', apply: '\\centering' },
  { label: '\\footnote', type: 'keyword', info: 'Fussnote', apply: '\\footnote{}' },
  { label: '\\url', type: 'keyword', info: 'URL', apply: '\\url{}' },
  { label: '\\href', type: 'keyword', info: 'Link', apply: '\\href{}{}' },
  { label: '\\title', type: 'keyword', info: 'Titel', apply: '\\title{}' },
  { label: '\\author', type: 'keyword', info: 'Autor', apply: '\\author{}' },
  { label: '\\date', type: 'keyword', info: 'Datum', apply: '\\date{}' },
  { label: '\\maketitle', type: 'keyword', info: 'Titelseite', apply: '\\maketitle' },
  { label: '\\tableofcontents', type: 'keyword', info: 'Inhaltsverzeichnis', apply: '\\tableofcontents' },
  { label: '\\newcommand', type: 'keyword', info: 'Neues Kommando', apply: '\\newcommand{}{}' },
  { label: '\\renewcommand', type: 'keyword', info: 'Kommando aendern', apply: '\\renewcommand{}{}' },
  { label: '\\input', type: 'keyword', info: 'Datei einfügen', apply: '\\input{}' },
  { label: '\\include', type: 'keyword', info: 'Datei einbinden', apply: '\\include{}' },
  { label: '\\frac', type: 'function', info: 'Bruch', apply: '\\frac{}{}' },
  { label: '\\sqrt', type: 'function', info: 'Wurzel', apply: '\\sqrt{}' },
  { label: '\\sum', type: 'keyword', info: 'Summe', apply: '\\sum' },
  { label: '\\int', type: 'keyword', info: 'Integral', apply: '\\int' }
]

const latexEnvironmentNames = [
  'itemize',
  'enumerate',
  'description',
  'figure',
  'table',
  'tabular',
  'equation',
  'align',
  'quote',
  'verbatim',
  'center'
]

function latexCompletionSource(context) {
  const envMatch = context.matchBefore(/\\(begin|end)\{[A-Za-z]*$/)
  if (envMatch) {
    const braceIndex = envMatch.text.lastIndexOf('{')
    const from = braceIndex >= 0 ? envMatch.from + braceIndex + 1 : envMatch.from
    if (from === context.pos && !context.explicit) return null
    const options = latexEnvironmentNames.map((env) => ({
      label: env,
      type: 'keyword',
      apply: env
    }))
    return {
      from,
      options,
      validFor: /^[A-Za-z]*$/
    }
  }

  const word = context.matchBefore(/\\[A-Za-z]*$/)
  if (!word || (word.from === word.to && !context.explicit)) return null
  return {
    from: word.from,
    options: latexCommandCompletions,
    validFor: /^\\[A-Za-z]*$/
  }
}

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

function isValidHexColor(value) {
  return typeof value === 'string' && /^#[0-9a-fA-F]{6}$/.test(value)
}

function updateLocalUserColor(newColor) {
  if (!newColor || !users.value) return
  const next = { ...users.value }
  let updated = false
  for (const [userId, user] of Object.entries(next)) {
    if (user?.username === username.value) {
      next[userId] = { ...user, color: newColor }
      updated = true
    }
  }
  if (updated) {
    users.value = next
  }
}

function applyCollabColorChange(newColor) {
  if (!isValidHexColor(newColor)) return
  updateLocalUserColor(newColor)
  if (!ydoc.value || !ytext) {
    updateDecorations()
    return
  }

  ydoc.value.transact(() => {
    let pos = 0
    const delta = ytext.toDelta()
    for (const op of delta) {
      const insert = op?.insert
      const text = typeof insert === 'string' ? insert : ''
      const length = text.length
      if (length > 0 && op?.attributes?.collabUser === username.value) {
        ytext.format(pos, length, { collabColor: newColor })
      }
      pos += length
    }

    if (yhighlights) {
      yhighlights.forEach((value, key) => {
        if (value?.username === username.value) {
          yhighlights.set(String(key), { ...value, color: newColor })
        }
      })
    }
  }, 'color')

  updateDecorations()
}

function buildInsertDecorations() {
  if (!ytext || !view.value) return []
  const decorations = []
  let pos = 0
  const delta = ytext.toDelta()

  for (const op of delta) {
    const insert = op?.insert
    const text = typeof insert === 'string' ? insert : ''
    const length = text.length
    const attrs = op?.attributes || {}
    const color = attrs.collabColor || attrs.color

    if (length > 0 && isValidHexColor(color)) {
      const safeFrom = clampPos(pos, view.value.state.doc.length)
      const safeTo = clampPos(pos + length, view.value.state.doc.length)
      if (safeFrom < safeTo) {
        const background = rgbaFromHex(color, 0.35)
        const outline = rgbaFromHex(color, 0.5)
        decorations.push(
          Decoration.mark({
            attributes: {
              style: `background: ${background}; border-radius: 2px; box-shadow: 0 0 0 1px ${outline}; text-decoration: underline; text-decoration-color: ${color}; text-underline-offset: 2px;`
            }
          }).range(safeFrom, safeTo)
        )
      }
    }

    pos += length
  }

  return decorations
}

function buildCommentDecorations() {
  if (!view.value) return []
  const list = Array.isArray(props.comments) ? props.comments : []
  if (!list.length) return []
  const decos = []
  const docLen = view.value.state.doc.length
  for (const comment of list) {
    if (!comment) continue
    const from = clampPos(comment.range_start, docLen)
    const to = clampPos(comment.range_end, docLen)
    if (from >= to) continue
    const classes = ['cm-comment-range']
    if (comment.resolved_at) classes.push('cm-comment-range-resolved')
    if (comment.id === props.activeCommentId) classes.push('cm-comment-range-active')
    decos.push(
      Decoration.mark({
        class: classes.join(' '),
        attributes: { 'data-comment-id': String(comment.id || '') }
      }).range(from, to)
    )
  }
  return decos
}

function updateDecorations() {
  if (!view.value) return
  if (applyingDecorations) return
  const decorations = []

  // Convert Yjs Map to plain object for line-level activity indicators
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

  // Character-level git diff (for summary + deleted-line gutter)
  const currentContent = view.value.state.doc.toString()
  const diffs = computeCharacterDiffs(currentContent)

  const insertDecorations = buildInsertDecorations()
  const includeInsertDecorations = insertDecorations.length === 0
  if (diffs.length > 0) {
    const { decorations: diffDecos, deletedLines } = diffsToDecorations(
      diffs,
      view.value,
      null,
      { includeInsertDecorations }
    )
    if (includeInsertDecorations) {
      decorations.push(...diffDecos)
    }
    deletedLinesRef.value = deletedLines
  } else {
    deletedLinesRef.value = new Set()
  }

  if (insertDecorations.length > 0) {
    decorations.push(...insertDecorations)
  }

  const commentDecorations = buildCommentDecorations()
  if (commentDecorations.length > 0) {
    decorations.push(...commentDecorations)
  }

  // Real-time activity indicator: subtle left border to show who is editing
  // This does NOT replace character-level highlighting, just adds a visual cue
  const now = Date.now()
  const HIGHLIGHT_DURATION_MS = 15000 // 15 seconds
  const myUsername = username.value

  for (const [lineNoStr, meta] of Object.entries(highlightsData)) {
    if (!meta || !meta.ts || !meta.color) continue

    // Only show other users' recent edits (not own edits)
    if (meta.username === myUsername) continue
    if (now - meta.ts > HIGHLIGHT_DURATION_MS) continue

    const lineNo = parseInt(lineNoStr, 10)
    if (isNaN(lineNo) || lineNo < 1 || lineNo > view.value.state.doc.lines) continue

    try {
      const line = view.value.state.doc.line(lineNo)
      // Only add a subtle left border - NO background to not interfere with character highlighting
      decorations.push(
        Decoration.line({
          attributes: {
            style: `border-left: 3px solid ${meta.color}; margin-left: -3px;`
          }
        }).range(line.from)
      )
    } catch {
      // Line might not exist
    }
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
  // Ensure we always have a valid color
  let userColor = collabColor.value
  if (!userColor && socket.value?.id && users.value?.[socket.value.id]) {
    userColor = users.value[socket.value.id].color
  }
  if (!userColor) {
    userColor = '#4ECDC4' // Fallback teal
  }

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

function scheduleCursorChange() {
  if (!view.value) return
  if (cursorChangeTimer) clearTimeout(cursorChangeTimer)
  cursorChangeTimer = setTimeout(() => {
    if (!view.value) return
    const sel = view.value.state.selection.main
    const lineInfo = view.value.state.doc.lineAt(sel.head)
    emit('cursor-change', {
      line: lineInfo.number,
      column: sel.head - lineInfo.from + 1
    })
  }, 120)
}

function emitSyncRequestFromEvent(event, cmView) {
  const pos = cmView.posAtCoords({ x: event.clientX, y: event.clientY })
  if (pos == null) return false
  const lineInfo = cmView.state.doc.lineAt(pos)
  emit('sync-request', {
    line: lineInfo.number,
    column: pos - lineInfo.from + 1
  })
  return false
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
      keymap.of([...defaultKeymap, ...historyKeymap, ...completionKeymap, indentWithTab]),
      StreamLanguage.define(stex),
      syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
      autocompletion({
        override: [latexCompletionSource]
      }),
      EditorView.lineWrapping,
      EditorView.domEventHandlers({
        dblclick: (event, cmView) => emitSyncRequestFromEvent(event, cmView)
      }),
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

          if (update.selectionSet) {
            scheduleCursorUpdate()
            scheduleCursorChange()
          }

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
          let userColor = collabColor.value
          if (!userColor && socket.value?.id && users.value?.[socket.value.id]) {
            userColor = users.value[socket.value.id].color
          }
          if (!userColor) {
            userColor = '#4ECDC4'
          }
          const userAttrs = { collabColor: userColor, collabUser: username.value }
          ydoc.value.transact(() => {
            // Apply in reverse order to keep positions stable
            changes.sort((a, b) => b.from - a.from)
            for (const ch of changes) {
              const delLen = ch.to - ch.from
              if (delLen > 0) ytext.delete(ch.from, delLen)
              if (ch.insert) ytext.insert(ch.from, ch.insert, userAttrs)
            }
            updateLocalHighlights(update)
          }, 'cm')

          emit('content-change', update.state.doc.toString())
          updateDecorations()

          // Analytics: Track typing burst
          const insertedChars = changes.reduce((sum, ch) => sum + (ch.insert?.length || 0), 0)
          if (insertedChars > 0) {
            typingMetrics.recordInput(insertedChars)
          }
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
    if (ytext && ytext.length > 0) {
      ytext.format(0, ytext.length, { collabColor: null, collabUser: null })
    }
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

function getSelectionRange() {
  if (!view.value) return null
  const sel = view.value.state.selection.main
  return { from: sel.from, to: sel.to }
}

function getSelectionText() {
  if (!view.value) return ''
  const sel = view.value.state.selection.main
  if (sel.from === sel.to) return ''
  return view.value.state.doc.sliceString(sel.from, sel.to)
}

function refresh() {
  view.value?.requestMeasure?.()
}

function jumpToLine(line, column = 1) {
  if (!view.value) return
  const totalLines = view.value.state.doc.lines
  const safeLine = Math.max(1, Math.min(Number(line) || 1, totalLines))
  const lineInfo = view.value.state.doc.line(safeLine)
  const safeColumn = Math.max(1, Number(column) || 1)
  const pos = Math.min(lineInfo.to, lineInfo.from + safeColumn - 1)
  view.value.dispatch({
    selection: { anchor: pos },
    effects: EditorView.scrollIntoView(pos, { y: 'center' })
  })
  view.value.focus()
}

defineExpose({
  clearHighlights,
  refresh,
  refreshBaseline,
  getCurrentContent,
  getSelectionRange,
  getSelectionText,
  jumpToLine
})

// Callback for when another user updates their color
function onColorUpdate(userId, newColor) {
  // Update the remote cursor color if it exists
  if (remoteCursors.value[userId]) {
    remoteCursors.value[userId] = {
      ...remoteCursors.value[userId],
      color: newColor
    }
  }
  // Update decorations to reflect new color
  updateDecorations()
}

const collaboration = useYjsCollaboration(roomId, username.value, processYDoc, onUpdateCursor, {
  autoSync: true,
  onColorUpdate
})
const { ydoc, socket, users, updateColor } = collaboration

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

watch(
  () => props.comments,
  () => {
    updateDecorations()
  },
  { deep: true }
)

watch(
  () => props.activeCommentId,
  () => {
    updateDecorations()
  }
)

// Watch for collab color changes (when user updates their color in settings)
watch(
  () => collabColor.value,
  (newColor) => {
    if (!newColor) return
    applyCollabColorChange(newColor)
    if (socket.value?.connected) {
      // Broadcast color change to other users
      updateColor(newColor)
    }
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
  if (cursorChangeTimer) clearTimeout(cursorChangeTimer)
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
  background: rgba(var(--v-theme-success), 0.2);
  border-radius: 2px;
  box-shadow: 0 0 0 1px rgba(var(--v-theme-success), 0.45);
  text-decoration: underline;
  text-decoration-color: rgb(var(--v-theme-success));
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

/* Comment ranges */
:global(.cm-comment-range) {
  background: rgba(var(--v-theme-warning), 0.18);
  border-bottom: 2px solid rgba(var(--v-theme-warning), 0.6);
  border-radius: 2px;
}

:global(.cm-comment-range-resolved) {
  background: rgba(var(--v-theme-surface-variant), 0.35);
  border-bottom: 2px solid rgba(var(--v-theme-on-surface), 0.35);
}

:global(.cm-comment-range-active) {
  background: rgba(var(--v-theme-warning), 0.32);
  box-shadow: inset 0 -2px 0 rgba(var(--v-theme-warning), 0.75);
}

/* Real-time user edit line highlighting */
:global(.cm-user-edit-line) {
  transition: background-color 0.3s ease, border-color 0.3s ease;
}
</style>
