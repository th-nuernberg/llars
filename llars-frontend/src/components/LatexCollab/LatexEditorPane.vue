<template>
  <div class="editor-pane">
    <!-- Quick Formatting Toolbar (Overleaf-style) -->
    <div v-if="!readonly" class="formatting-toolbar" :class="{ collapsed: toolbarCollapsed }">
      <!-- Toggle button -->
      <v-tooltip location="bottom">
        <template #activator="{ props: tp }">
          <button v-bind="tp" class="toolbar-toggle-btn" @click="toggleToolbar">
            <LIcon size="14">{{ toolbarCollapsed ? 'mdi-chevron-down' : 'mdi-chevron-up' }}</LIcon>
          </button>
        </template>
        <span>{{ toolbarCollapsed ? $t('latexCollab.editor.toolbar.show') : $t('latexCollab.editor.toolbar.hide') }}</span>
      </v-tooltip>

      <!-- Collapsed state: just show label -->
      <span v-if="toolbarCollapsed" class="toolbar-collapsed-label" @click="toggleToolbar">
        {{ $t('latexCollab.editor.toolbar.label') }}
      </span>

      <!-- Expanded toolbar content -->
      <template v-if="!toolbarCollapsed">
        <!-- Text Formatting -->
        <div class="toolbar-group">
          <v-tooltip v-for="btn in textFormatButtons" :key="btn.id" location="bottom">
            <template #activator="{ props: tp }">
              <button v-bind="tp" class="toolbar-btn" @click="insertSnippet(btn.snippet, btn.wrap)">
                <LIcon size="16">{{ btn.icon }}</LIcon>
              </button>
            </template>
            <span>{{ btn.label }} <kbd v-if="btn.shortcut">{{ btn.shortcut }}</kbd></span>
          </v-tooltip>
        </div>

        <div class="toolbar-divider" />

        <!-- Structure -->
        <div class="toolbar-group">
          <v-tooltip v-for="btn in structureButtons" :key="btn.id" location="bottom">
            <template #activator="{ props: tp }">
              <button v-bind="tp" class="toolbar-btn" @click="insertSnippet(btn.snippet, btn.wrap)">
                <LIcon size="16">{{ btn.icon }}</LIcon>
              </button>
            </template>
            <span>{{ btn.label }}</span>
          </v-tooltip>
        </div>

        <div class="toolbar-divider" />

        <!-- Lists -->
        <div class="toolbar-group">
          <v-tooltip v-for="btn in listButtons" :key="btn.id" location="bottom">
            <template #activator="{ props: tp }">
              <button v-bind="tp" class="toolbar-btn" @click="insertSnippet(btn.snippet, btn.wrap)">
                <LIcon size="16">{{ btn.icon }}</LIcon>
              </button>
            </template>
            <span>{{ btn.label }}</span>
          </v-tooltip>
        </div>

        <div class="toolbar-divider" />

        <!-- Content (Figure, Table) -->
        <div class="toolbar-group">
          <template v-for="btn in contentButtons" :key="btn.id">
            <!-- Special table button with size picker -->
            <v-menu v-if="btn.hasMenu" v-model="showTablePicker" :close-on-content-click="false" location="bottom">
              <template #activator="{ props: menuProps }">
                <v-tooltip location="bottom">
                  <template #activator="{ props: tp }">
                    <button v-bind="{ ...tp, ...menuProps }" class="toolbar-btn">
                      <LIcon size="16">{{ btn.icon }}</LIcon>
                    </button>
                  </template>
                  <span>{{ btn.label }}</span>
                </v-tooltip>
              </template>
              <v-card class="table-picker-card" min-width="200">
                <v-card-text class="pa-3">
                  <div class="text-subtitle-2 mb-2">{{ $t('latexCollab.editor.table.size') }}</div>
                  <div class="d-flex align-center ga-3 mb-2">
                    <v-text-field
                      v-model.number="tableRows"
                      :label="$t('latexCollab.editor.table.rows')"
                      type="number"
                      min="1"
                      max="20"
                      density="compact"
                      hide-details
                      variant="outlined"
                      style="max-width: 70px"
                    />
                    <span class="text-body-2">×</span>
                    <v-text-field
                      v-model.number="tableCols"
                      :label="$t('latexCollab.editor.table.columns')"
                      type="number"
                      min="1"
                      max="10"
                      density="compact"
                      hide-details
                      variant="outlined"
                      style="max-width: 70px"
                    />
                  </div>
                  <div class="text-caption text-medium-emphasis mb-2">
                    {{ $t('latexCollab.editor.table.preview', { rows: tableRows, cols: tableCols }) }}
                  </div>
                  <v-btn color="primary" size="small" block @click="insertTable">
                    <LIcon start size="small">mdi-table-plus</LIcon>
                    {{ $t('latexCollab.editor.table.insert') }}
                  </v-btn>
                </v-card-text>
              </v-card>
            </v-menu>
            <!-- Regular buttons -->
            <v-tooltip v-else location="bottom">
              <template #activator="{ props: tp }">
                <button v-bind="tp" class="toolbar-btn" @click="insertSnippet(btn.snippet, btn.wrap)">
                  <LIcon size="16">{{ btn.icon }}</LIcon>
                </button>
              </template>
              <span>{{ btn.label }}</span>
            </v-tooltip>
          </template>
        </div>

        <div class="toolbar-divider" />

        <!-- Math -->
        <div class="toolbar-group">
          <v-tooltip v-for="btn in mathButtons" :key="btn.id" location="bottom">
            <template #activator="{ props: tp }">
              <button v-bind="tp" class="toolbar-btn" @click="insertSnippet(btn.snippet, btn.wrap)">
                <LIcon size="16">{{ btn.icon }}</LIcon>
              </button>
            </template>
            <span>{{ btn.label }}</span>
          </v-tooltip>
        </div>

        <div class="toolbar-divider" />

        <!-- References -->
        <div class="toolbar-group">
          <v-tooltip v-for="btn in refButtons" :key="btn.id" location="bottom">
            <template #activator="{ props: tp }">
              <button v-bind="tp" class="toolbar-btn" @click="insertSnippet(btn.snippet, btn.wrap)">
                <LIcon size="16">{{ btn.icon }}</LIcon>
              </button>
            </template>
            <span>{{ btn.label }}</span>
          </v-tooltip>
        </div>
      </template>
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
/**
 * LatexEditorPane
 *
 * Collaborative LaTeX editor component with real-time synchronization via Yjs.
 * Features:
 * - CodeMirror 6 with LaTeX syntax highlighting
 * - Real-time collaboration with remote cursor display
 * - Git-like diff visualization
 * - AI ghost text completions (optional)
 * - Rich formatting toolbar (Overleaf-style)
 * - Comment range highlighting
 *
 * @component LatexEditorPane
 * @module LatexCollab
 */
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as Y from 'yjs'
import { EditorState, StateEffect, StateField, RangeSet } from '@codemirror/state'
import { EditorView, Decoration, highlightActiveLine, drawSelection, highlightSpecialChars, lineNumbers, keymap, gutter } from '@codemirror/view'
import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands'
import { autocompletion, completionKeymap } from '@codemirror/autocomplete'
import { stex } from '@codemirror/legacy-modes/mode/stex'
import { StreamLanguage, defaultHighlightStyle, syntaxHighlighting } from '@codemirror/language'
import { useI18n } from 'vue-i18n'

// External composables
import { useAuth } from '@/composables/useAuth'
import { useYjsCollaboration } from '@/components/PromptEngineering/composables/useYjsCollaboration'
import { useGitDiff } from '@/components/MarkdownCollab/composables/useGitDiff'
import { useTypingMetrics } from '@/composables/useAnalyticsMetrics'

// Local modules - constants (shared with LatexAI editor)
import {
  AI_COLLAB_COLOR,
  AI_COLLAB_USERNAME,
  LATEX_COMMAND_COMPLETIONS,
  LATEX_ENVIRONMENT_NAMES,
  AI_COMMAND_COMPLETIONS,
  TEXT_FORMAT_BUTTONS,
  STRUCTURE_BUTTONS,
  LIST_BUTTONS,
  CONTENT_BUTTONS,
  MATH_BUTTONS,
  REF_BUTTONS,
  generateTableSnippet
} from './LatexEditorPane/constants'

// Local modules - CodeMirror widgets (shared with LatexAI editor)
import { CaretWidget, GhostTextWidget, deletionMarkerInstance, setDeletionMarkerLabel } from './LatexEditorPane/widgets'

const props = defineProps({
  document: { type: Object, required: true },
  readonly: { type: Boolean, default: false },
  comments: { type: Array, default: () => [] },
  activeCommentId: { type: Number, default: null },
  aiEnabled: { type: Boolean, default: false },
  ghostTextEnabled: { type: Boolean, default: false },
  ghostTextDelay: { type: Number, default: 800 }
})

const emit = defineEmits(['content-change', 'git-summary', 'cursor-change', 'sync-request', 'ai-command', 'request-completion', 'update:ghostTextEnabled', 'document-saved'])

const { t, locale } = useI18n()

setDeletionMarkerLabel(t('latexCollab.editor.deletedText'))
watch(locale, () => {
  setDeletionMarkerLabel(t('latexCollab.editor.deletedText'))
})

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

// Ghost text (AI completion) state
const ghostText = ref('')
const ghostTextPosition = ref(null)
let ghostTextTimer = null
let ghostTextDecorationRange = null

function mapButtons(buttons, labels) {
  return buttons.map(btn => ({
    ...btn,
    label: labels[btn.id] || btn.label
  }))
}

const textFormatButtons = computed(() => mapButtons(TEXT_FORMAT_BUTTONS, {
  bold: t('latexCollab.editor.toolbar.bold'),
  italic: t('latexCollab.editor.toolbar.italic'),
  underline: t('latexCollab.editor.toolbar.underline'),
  emph: t('latexCollab.editor.toolbar.emph'),
  typewriter: t('latexCollab.editor.toolbar.typewriter')
}))

const structureButtons = computed(() => mapButtons(STRUCTURE_BUTTONS, {
  section: t('latexCollab.editor.toolbar.section'),
  subsection: t('latexCollab.editor.toolbar.subsection'),
  subsubsection: t('latexCollab.editor.toolbar.subsubsection'),
  paragraph: t('latexCollab.editor.toolbar.paragraph')
}))

const listButtons = computed(() => mapButtons(LIST_BUTTONS, {
  itemize: t('latexCollab.editor.toolbar.itemize'),
  enumerate: t('latexCollab.editor.toolbar.enumerate'),
  description: t('latexCollab.editor.toolbar.description')
}))

const contentButtons = computed(() => mapButtons(CONTENT_BUTTONS, {
  figure: t('latexCollab.editor.toolbar.figure'),
  table: t('latexCollab.editor.toolbar.table'),
  code: t('latexCollab.editor.toolbar.code'),
  quote: t('latexCollab.editor.toolbar.quote')
}))

const mathButtons = computed(() => mapButtons(MATH_BUTTONS, {
  'inline-math': t('latexCollab.editor.toolbar.inlineMath'),
  'display-math': t('latexCollab.editor.toolbar.displayMath'),
  equation: t('latexCollab.editor.toolbar.equation'),
  align: t('latexCollab.editor.toolbar.align'),
  frac: t('latexCollab.editor.toolbar.frac')
}))

const refButtons = computed(() => mapButtons(REF_BUTTONS, {
  cite: t('latexCollab.editor.toolbar.cite'),
  ref: t('latexCollab.editor.toolbar.ref'),
  label: t('latexCollab.editor.toolbar.label'),
  footnote: t('latexCollab.editor.toolbar.footnote'),
  url: t('latexCollab.editor.toolbar.url')
}))

const latexCommandInfo = computed(() => ({
  '\\documentclass': t('latexCollab.completions.documentclass'),
  '\\usepackage': t('latexCollab.completions.usepackage'),
  '\\begin': t('latexCollab.completions.begin'),
  '\\end': t('latexCollab.completions.end'),
  '\\section': t('latexCollab.completions.section'),
  '\\subsection': t('latexCollab.completions.subsection'),
  '\\subsubsection': t('latexCollab.completions.subsubsection'),
  '\\paragraph': t('latexCollab.completions.paragraph'),
  '\\textbf': t('latexCollab.completions.textbf'),
  '\\textit': t('latexCollab.completions.textit'),
  '\\emph': t('latexCollab.completions.emph'),
  '\\underline': t('latexCollab.completions.underline'),
  '\\item': t('latexCollab.completions.item'),
  '\\label': t('latexCollab.completions.label'),
  '\\ref': t('latexCollab.completions.ref'),
  '\\pageref': t('latexCollab.completions.pageref'),
  '\\cite': t('latexCollab.completions.cite'),
  '\\citet': t('latexCollab.completions.citet'),
  '\\citep': t('latexCollab.completions.citep'),
  '\\includegraphics': t('latexCollab.completions.includegraphics'),
  '\\caption': t('latexCollab.completions.caption'),
  '\\centering': t('latexCollab.completions.centering'),
  '\\footnote': t('latexCollab.completions.footnote'),
  '\\url': t('latexCollab.completions.url'),
  '\\href': t('latexCollab.completions.href'),
  '\\title': t('latexCollab.completions.title'),
  '\\author': t('latexCollab.completions.author'),
  '\\date': t('latexCollab.completions.date'),
  '\\maketitle': t('latexCollab.completions.maketitle'),
  '\\tableofcontents': t('latexCollab.completions.tableofcontents'),
  '\\newcommand': t('latexCollab.completions.newcommand'),
  '\\renewcommand': t('latexCollab.completions.renewcommand'),
  '\\input': t('latexCollab.completions.input'),
  '\\include': t('latexCollab.completions.include'),
  '\\frac': t('latexCollab.completions.frac'),
  '\\sqrt': t('latexCollab.completions.sqrt'),
  '\\sum': t('latexCollab.completions.sum'),
  '\\int': t('latexCollab.completions.int')
}))

const latexCommandCompletions = computed(() => (
  LATEX_COMMAND_COMPLETIONS.map(cmd => ({
    ...cmd,
    info: latexCommandInfo.value[cmd.label] || cmd.info
  }))
))

const aiCommandInfo = computed(() => ({
  '@ai': t('latexCollab.aiCommands.ai'),
  '@rewrite': t('latexCollab.aiCommands.rewrite'),
  '@expand': t('latexCollab.aiCommands.expand'),
  '@summarize': t('latexCollab.aiCommands.summarize'),
  '@fix': t('latexCollab.aiCommands.fix'),
  '@translate': t('latexCollab.aiCommands.translate'),
  '@cite': t('latexCollab.aiCommands.cite'),
  '@abstract': t('latexCollab.aiCommands.abstract'),
  '@titles': t('latexCollab.aiCommands.titles')
}))

const aiCommandCompletions = computed(() => (
  AI_COMMAND_COMPLETIONS.map(cmd => ({
    ...cmd,
    info: aiCommandInfo.value[cmd.label] || cmd.info
  }))
))

const { tokenParsed, collabColor } = useAuth()
const username = computed(() => tokenParsed.value?.preferred_username || localStorage.getItem('username') || t('latexCollab.editor.userFallback'))

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
  getInsertRanges,
  diffsToDecorations,
  hasChanges,
  getChangeSummary,
  updateBaseline
} = useGitDiff({ apiPrefix: '/api/latex-collab' })

// Track deleted lines for gutter markers
const deletedLinesRef = ref(new Set())

// =============================================================================
// TOOLBAR STATE
// =============================================================================

// Table size picker state
const showTablePicker = ref(false)
const tableRows = ref(3)
const tableCols = ref(3)

// Toolbar collapsed state (persisted in localStorage)
// Default to collapsed unless user explicitly expanded it before
const toolbarCollapsed = ref(localStorage.getItem('latex-toolbar-collapsed') !== 'false')

/**
 * Toggle toolbar visibility and persist preference
 */
function toggleToolbar() {
  toolbarCollapsed.value = !toolbarCollapsed.value
  localStorage.setItem('latex-toolbar-collapsed', toolbarCollapsed.value)
}

/**
 * Insert a table with the specified dimensions
 */
function insertTable() {
  const snippet = generateTableSnippet(tableRows.value, tableCols.value)
  insertSnippet(snippet, false)
  showTablePicker.value = false
}

/**
 * LaTeX command and environment autocompletion source.
 * Provides completions for \commands and environment names within \begin{}/\end{}.
 *
 * @param {CompletionContext} context - CodeMirror completion context
 * @returns {CompletionResult|null} Completion result or null if no match
 */
function latexCompletionSource(context) {
  // Check for environment name completion inside \begin{} or \end{}
  const envMatch = context.matchBefore(/\\(begin|end)\{[A-Za-z]*$/)
  if (envMatch) {
    const braceIndex = envMatch.text.lastIndexOf('{')
    const from = braceIndex >= 0 ? envMatch.from + braceIndex + 1 : envMatch.from
    if (from === context.pos && !context.explicit) return null
    const options = LATEX_ENVIRONMENT_NAMES.map((env) => ({
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

  // Check for LaTeX command completion (starting with \)
  const word = context.matchBefore(/\\[A-Za-z]*$/)
  if (!word || (word.from === word.to && !context.explicit)) return null
  return {
    from: word.from,
    options: latexCommandCompletions.value,
    validFor: /^\\[A-Za-z]*$/
  }
}

/**
 * AI @-command completion source.
 * Only active when aiEnabled prop is true.
 * Provides completions for AI commands like @ai, @rewrite, @expand, etc.
 *
 * @param {CompletionContext} context - CodeMirror completion context
 * @returns {CompletionResult|null} Completion result or null if no match
 */
function aiCompletionSource(context) {
  if (!props.aiEnabled) return null

  // Match @-commands
  const word = context.matchBefore(/@[A-Za-z]*$/)
  if (!word || (word.from === word.to && !context.explicit)) return null

  return {
    from: word.from,
    options: aiCommandCompletions.value,
    validFor: /^@[A-Za-z]*$/
  }
}

// Handle Enter key to execute @-commands
function handleEnterForAICommand(view) {
  if (!props.aiEnabled) return false

  // Get current line
  const { state } = view
  const pos = state.selection.main.head
  const line = state.doc.lineAt(pos)
  const lineText = line.text.trim()

  // Check if line starts with @-command
  const cmdMatch = lineText.match(/^@(\w+)(?:\s+(.*))?$/)
  if (!cmdMatch) return false

  const command = cmdMatch[1].toLowerCase()
  const args = (cmdMatch[2] || '').trim()

  // Get selected text if any
  const sel = state.selection.main
  const selectedText = sel.from !== sel.to ? state.doc.sliceString(sel.from, sel.to) : ''

  // Commands that work on selection
  const selectionCommands = ['rewrite', 'expand', 'summarize', 'fix', 'translate', 'cite']

  // If command needs selection but none provided, don't execute
  if (selectionCommands.includes(command) && !selectedText && !args) {
    return false
  }

  // Emit command for parent to handle
  emit('ai-command', {
    command,
    args,
    selectedText,
    lineFrom: line.from,
    lineTo: line.to
  })

  return true // Prevent default Enter behavior
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

// =============================================================================
// EDITOR STATE FLAGS
// =============================================================================

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

function buildInsertDecorations(insertRanges = []) {
  if (!ytext || !view.value || insertRanges.length === 0) return []
  const decorations = []
  let pos = 0
  let rangeIndex = 0
  const delta = ytext.toDelta()
  const docLen = view.value.state.doc.length

  for (const op of delta) {
    const insert = op?.insert
    const text = typeof insert === 'string' ? insert : ''
    const length = text.length
    const attrs = op?.attributes || {}
    const color = attrs.collabColor || attrs.color
    if (length === 0) continue

    const segmentStart = pos
    const segmentEnd = pos + length

    while (rangeIndex < insertRanges.length && insertRanges[rangeIndex].to <= segmentStart) {
      rangeIndex += 1
    }

    let idx = rangeIndex
    while (idx < insertRanges.length && insertRanges[idx].from < segmentEnd) {
      const range = insertRanges[idx]
      const overlapFrom = Math.max(segmentStart, range.from)
      const overlapTo = Math.min(segmentEnd, range.to)
      if (overlapFrom < overlapTo) {
        const safeFrom = clampPos(overlapFrom, docLen)
        const safeTo = clampPos(overlapTo, docLen)
        if (safeFrom < safeTo) {
          if (isValidHexColor(color)) {
            const background = rgbaFromHex(color, 0.35)
            const outline = rgbaFromHex(color, 0.5)
            decorations.push(
              Decoration.mark({
                attributes: {
                  style: `background: ${background}; border-radius: 2px; box-shadow: 0 0 0 1px ${outline}; text-decoration: underline; text-decoration-color: ${color}; text-underline-offset: 2px;`
                }
              }).range(safeFrom, safeTo)
            )
          } else {
            decorations.push(
              Decoration.mark({ class: 'cm-diff-insert' }).range(safeFrom, safeTo)
            )
          }
        }
      }
      if (range.to <= segmentEnd) {
        idx += 1
      } else {
        break
      }
    }

    rangeIndex = idx

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
  const insertRanges = getInsertRanges(diffs)

  const insertDecorations = buildInsertDecorations(insertRanges)
  if (diffs.length > 0) {
    const { decorations: diffDecos, deletedLines } = diffsToDecorations(
      diffs,
      view.value,
      null,
      { includeInsertDecorations: false }
    )
    decorations.push(...diffDecos)
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

  // Ghost text decoration (AI completion suggestion)
  if (ghostText.value && ghostTextPosition.value !== null && ghostTextPosition.value <= docLen) {
    decorations.push(
      Decoration.widget({
        widget: new GhostTextWidget(ghostText.value),
        side: 1
      }).range(ghostTextPosition.value)
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
    const u = meta?.username || t('latexCollab.editor.userUnknown')
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

// Ghost text (AI completion) functions
function scheduleGhostTextRequest() {
  if (!props.ghostTextEnabled || !props.aiEnabled || !view.value) return

  // Cancel any pending request
  cancelGhostText()

  ghostTextTimer = setTimeout(() => {
    if (!view.value) return

    const pos = view.value.state.selection.main.head
    const doc = view.value.state.doc

    // Get context around cursor (500 chars before, 200 after)
    const contextStart = Math.max(0, pos - 500)
    const contextEnd = Math.min(doc.length, pos + 200)
    const beforeCursor = doc.sliceString(contextStart, pos)
    const afterCursor = doc.sliceString(pos, contextEnd)
    const context = beforeCursor + '[CURSOR]' + afterCursor

    // Emit request for parent to handle via AI service
    emit('request-completion', {
      context,
      cursorPosition: beforeCursor.length,
      documentPosition: pos
    })
  }, props.ghostTextDelay)
}

function setGhostText(text, position) {
  if (!view.value || !text) {
    cancelGhostText()
    return
  }

  // Verify position is still valid
  const currentPos = view.value.state.selection.main.head
  if (position !== currentPos) {
    // Cursor moved, don't show ghost text
    return
  }

  ghostText.value = text
  ghostTextPosition.value = position
  updateDecorations()
}

function acceptGhostText() {
  if (!ghostText.value || ghostTextPosition.value === null || !view.value || !ytext) {
    return false
  }

  const text = ghostText.value
  const position = ghostTextPosition.value

  // Insert via Yjs with AI collab attributes so it shows as AI-generated
  const aiAttrs = { collabColor: AI_COLLAB_COLOR, collabUser: AI_COLLAB_USERNAME }

  skipNextTextSync = true
  ydoc.value.transact(() => {
    ytext.insert(position, text, aiAttrs)
  }, 'ai')

  // Update CodeMirror view to reflect the change
  view.value.dispatch({
    changes: {
      from: position,
      to: position,
      insert: text
    },
    selection: { anchor: position + text.length }
  })

  cancelGhostText()
  return true
}

function cancelGhostText() {
  if (ghostTextTimer) {
    clearTimeout(ghostTextTimer)
    ghostTextTimer = null
  }
  ghostText.value = ''
  ghostTextPosition.value = null
  updateDecorations()
}

function toggleGhostText() {
  emit('update:ghostTextEnabled', !props.ghostTextEnabled)
}

/**
 * Insert a LaTeX snippet at the current cursor position
 * @param {string} snippet - The LaTeX snippet to insert (with $CURSOR$ and $SEL$ placeholders)
 * @param {boolean} wrap - If true, wrap selected text with the snippet
 */
function insertSnippet(snippet, wrap = false) {
  if (!view.value || !ytext || props.readonly) return

  const state = view.value.state
  const sel = state.selection.main
  const selectedText = sel.from !== sel.to ? state.doc.sliceString(sel.from, sel.to) : ''

  let insertText = snippet
  let cursorOffset = 0

  if (wrap && selectedText) {
    // Replace $SEL$ with the selected text
    insertText = snippet.replace(/\$SEL\$/g, selectedText)
    // Cursor goes to end of insertion
    cursorOffset = insertText.length
  } else if (wrap) {
    // No selection, but wrap mode - replace $SEL$ with empty and position cursor there
    const selPos = snippet.indexOf('$SEL$')
    if (selPos !== -1) {
      insertText = snippet.replace(/\$SEL\$/g, '')
      cursorOffset = selPos
    } else {
      cursorOffset = insertText.length
    }
  } else {
    // Replace $CURSOR$ placeholder and position cursor there
    const cursorPos = snippet.indexOf('$CURSOR$')
    if (cursorPos !== -1) {
      insertText = snippet.replace(/\$CURSOR\$/g, '')
      cursorOffset = cursorPos
    } else {
      cursorOffset = insertText.length
    }
  }

  // Get user color for collab highlighting
  let userColor = collabColor.value
  if (!userColor && socket.value?.id && users.value?.[socket.value.id]) {
    userColor = users.value[socket.value.id].color
  }
  if (!userColor) {
    userColor = '#4ECDC4'
  }
  const userAttrs = { collabColor: userColor, collabUser: username.value }

  // Insert via Yjs
  skipNextTextSync = true
  ydoc.value.transact(() => {
    // Delete selection if any
    if (sel.from !== sel.to) {
      ytext.delete(sel.from, sel.to - sel.from)
    }
    // Insert the snippet
    ytext.insert(sel.from, insertText, userAttrs)
  }, 'cm')

  // Update CodeMirror view
  const newCursorPos = sel.from + cursorOffset
  view.value.dispatch({
    changes: {
      from: sel.from,
      to: sel.to,
      insert: insertText
    },
    selection: { anchor: newCursorPos }
  })

  // Focus the editor
  view.value.focus()
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
      // Custom keymaps for ghost text and AI commands
      keymap.of([
        // Tab: Accept ghost text if available, otherwise default behavior
        {
          key: 'Tab',
          run: () => {
            if (ghostText.value && ghostTextPosition.value !== null) {
              return acceptGhostText()
            }
            return false // Let default Tab behavior (indent) happen
          }
        },
        // Escape: Dismiss ghost text
        {
          key: 'Escape',
          run: () => {
            if (ghostText.value) {
              cancelGhostText()
              return true
            }
            return false
          }
        },
        // Enter: Execute @-command if on an @-command line
        {
          key: 'Enter',
          run: (cmView) => handleEnterForAICommand(cmView)
        },
        // Ctrl+B: Bold
        {
          key: 'Mod-b',
          run: () => {
            insertSnippet('\\textbf{$SEL$}', true)
            return true
          }
        },
        // Ctrl+I: Italic
        {
          key: 'Mod-i',
          run: () => {
            insertSnippet('\\textit{$SEL$}', true)
            return true
          }
        },
        // Ctrl+U: Underline
        {
          key: 'Mod-u',
          run: () => {
            insertSnippet('\\underline{$SEL$}', true)
            return true
          }
        },
        ...defaultKeymap,
        ...historyKeymap,
        ...completionKeymap,
        indentWithTab
      ]),
      StreamLanguage.define(stex),
      syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
      autocompletion({
        override: props.aiEnabled
          ? [aiCompletionSource, latexCompletionSource]
          : [latexCompletionSource]
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
            // Cancel ghost text when cursor moves
            if (ghostText.value) {
              cancelGhostText()
            }
          }

          if (!update.docChanged || props.readonly) {
            updateDecorations()
            return
          }

          // Cancel ghost text on any document change
          if (ghostText.value) {
            cancelGhostText()
          }

          // Schedule new ghost text request after typing pause
          if (props.ghostTextEnabled && props.aiEnabled) {
            scheduleGhostTextRequest()
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
 * Replace the editor content with the provided text (used for rollback recovery).
 */
function replaceContent(nextText) {
  if (!ydoc.value || !ytext) return false
  const text = String(nextText ?? '')
  const current = ytext.toString()
  if (text === current) return true

  ydoc.value.transact(() => {
    if (current.length > 0) {
      ytext.delete(0, current.length)
    }
    if (text) {
      ytext.insert(0, text)
    }
  }, 'rollback')

  emit('content-change', text)
  emit('git-summary', computeGitSummary())
  return true
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

function flushDocumentState() {
  return new Promise((resolve) => {
    const sock = socket.value
    const room = roomId.value
    if (!sock || !room) {
      resolve(false)
      return
    }

    let finished = false
    const timeout = setTimeout(() => {
      if (finished) return
      finished = true
      resolve(false)
    }, 1200)

    sock.emit('flush_document', { room }, (response) => {
      if (finished) return
      clearTimeout(timeout)
      finished = true
      resolve(!!response?.success)
    })
  })
}

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

/**
 * Initialize Yjs collaboration with WebSocket connection.
 *
 * The onDocumentSaved callback enables real-time Git panel updates:
 * - YJS server saves document to DB after 2s debounce
 * - Server broadcasts `document_saved` to workspace room
 * - We forward this event to parent component (LatexCollabWorkspace)
 * - Parent refreshes Git panel via gitPanelRef.checkForChanges()
 *
 * Event flow: YJS Server → Socket.IO → useYjsCollaboration → EditorPane → Workspace → GitPanel
 */
const collaboration = useYjsCollaboration(roomId, username.value, processYDoc, onUpdateCursor, {
  autoSync: true,
  onColorUpdate,
  /**
   * Handle document_saved event from YJS server.
   * @param {Object} data - Event payload
   * @param {number} data.documentId - Saved document ID
   * @param {number} data.workspaceId - Workspace containing the document
   * @param {string} data.kind - Document type ('latex')
   * @param {number} data.contentLength - Content length in characters
   * @param {string} data.savedAt - ISO timestamp
   */
  onDocumentSaved: (data) => {
    console.log('[LatexEditorPane] document_saved, emitting to parent:', data)
    emit('document-saved', data)
  }
})
const { ydoc, socket, users, updateColor, switchRoom, reloadRoom, reloadAnyRoom } = collaboration

defineExpose({
  clearHighlights,
  refresh,
  refreshBaseline,
  replaceContent,
  getCurrentContent,
  getSelectionRange,
  getSelectionText,
  jumpToLine,
  flushDocumentState,
  reloadRoom,
  reloadAnyRoom,
  // Ghost text (AI completion) functions
  setGhostText,
  cancelGhostText,
  acceptGhostText,
  toggleGhostText,
  // Connection state for parent to display
  isConnected,
  activeUsers
})

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

// Watch for document changes to switch rooms without remounting the component
// This provides a smoother experience when switching between documents
let previousDocumentId = null
watch(
  () => props.document?.id,
  async (newId, oldId) => {
    // Skip initial mount (handled by onMounted)
    if (!previousDocumentId) {
      previousDocumentId = newId
      return
    }

    // Skip if same document
    if (newId === previousDocumentId) return

    const oldRoom = props.document?.yjs_doc_id || `latex_${previousDocumentId}`
    const newRoom = props.document?.yjs_doc_id || `latex_${newId}`
    previousDocumentId = newId

    // Clear remote cursors from old document
    remoteCursors.value = {}

    // Reset error state
    error.value = ''

    // Cancel any pending ghost text
    cancelGhostText()

    // Switch collaboration room (leaves old room, joins new room, creates fresh Yjs doc)
    switchRoom(oldRoom, newRoom)

    // Load new git baseline for diff comparison
    await loadBaseline(newId)

    // Wait for the server to send the snapshot
    // Give the socket time to receive and process the snapshot
    await new Promise(resolve => setTimeout(resolve, 100))
    await nextTick()

    // Process the new Yjs doc to emit content-change and update editor
    processYDoc()
    updateDecorations()
  },
  { immediate: false }
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

  // Clean up all timers to prevent memory leaks
  if (cursorSendTimer) clearTimeout(cursorSendTimer)
  if (cursorChangeTimer) clearTimeout(cursorChangeTimer)
  if (ghostTextTimer) {
    clearTimeout(ghostTextTimer)
    ghostTextTimer = null
  }

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
/**
 * LatexEditorPane Styles
 *
 * Imports shared styles from the LatexEditorPane module.
 * Includes editor layout, remote cursors, git diff highlighting,
 * comment ranges, and formatting toolbar styles.
 *
 * @see ./LatexEditorPane/styles/LatexEditorPane.css
 */
@import './LatexEditorPane/styles/LatexEditorPane.css';
</style>
