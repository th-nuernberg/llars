<template>
  <div class="diff-root">
    <div class="diff-header">
      <div class="diff-header__side">
        <span class="diff-header__label">Basis</span>
        <span class="diff-header__value">{{ baseLabel || '—' }}</span>
      </div>
      <div class="diff-header__side">
        <span class="diff-header__label">Vergleich</span>
        <span class="diff-header__value">{{ compareLabel || '—' }}</span>
      </div>
    </div>

    <div class="diff-body">
      <div v-if="rows.length === 0" class="diff-empty">
        Keine Unterschiede.
      </div>
      <div v-else class="diff-rows">
        <div
          v-for="row in rows"
          :key="row.key"
          class="diff-row"
          :class="row.type"
        >
          <div class="diff-line diff-line--left">{{ row.leftLine }}</div>
          <div class="diff-cell diff-cell--left" :class="row.leftClass">
            <span class="diff-text">
              <template v-if="row.leftSegments && row.leftSegments.length">
                <span
                  v-for="(segment, index) in row.leftSegments"
                  :key="`${row.key}-l-${index}`"
                  :class="segmentClass(segment.type, 'left')"
                >{{ segment.text }}</span>
              </template>
              <template v-else>{{ row.leftText }}</template>
            </span>
          </div>
          <div class="diff-line diff-line--right">{{ row.rightLine }}</div>
          <div class="diff-cell diff-cell--right" :class="row.rightClass">
            <span class="diff-text">
              <template v-if="row.rightSegments && row.rightSegments.length">
                <span
                  v-for="(segment, index) in row.rightSegments"
                  :key="`${row.key}-r-${index}`"
                  :class="segmentClass(segment.type, 'right')"
                >{{ segment.text }}</span>
              </template>
              <template v-else>{{ row.rightText }}</template>
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import DiffMatchPatch from 'diff-match-patch'

const props = defineProps({
  baseText: { type: String, default: '' },
  compareText: { type: String, default: '' },
  baseLabel: { type: String, default: '' },
  compareLabel: { type: String, default: '' }
})

const DIFF_DELETE = -1
const DIFF_INSERT = 1
const DIFF_EQUAL = 0

const dmp = new DiffMatchPatch()

function splitLines(value) {
  const lines = String(value ?? '').split('\n')
  if (lines.length > 0 && lines[lines.length - 1] === '') {
    lines.pop()
  }
  return lines
}

function buildInlineSegments(leftText, rightText) {
  const diffs = dmp.diff_main(leftText, rightText, false)
  dmp.diff_cleanupSemantic(diffs)
  const leftSegments = []
  const rightSegments = []

  for (const [op, text] of diffs) {
    if (!text) continue
    if (op === DIFF_EQUAL) {
      leftSegments.push({ type: 'equal', text })
      rightSegments.push({ type: 'equal', text })
    } else if (op === DIFF_DELETE) {
      leftSegments.push({ type: 'delete', text })
    } else if (op === DIFF_INSERT) {
      rightSegments.push({ type: 'insert', text })
    }
  }

  return { leftSegments, rightSegments }
}

function segmentClass(type, side) {
  if (type === 'delete' && side === 'left') return 'diff-inline diff-inline--delete'
  if (type === 'insert' && side === 'right') return 'diff-inline diff-inline--insert'
  return 'diff-inline'
}

const rows = computed(() => {
  const left = props.baseText ?? ''
  const right = props.compareText ?? ''
  if (left === right) return []

  const lineData = dmp.diff_linesToChars_(left, right)
  const diffs = dmp.diff_main(lineData.chars1, lineData.chars2, false)
  dmp.diff_charsToLines_(diffs, lineData.lineArray)

  const result = []
  let leftLine = 1
  let rightLine = 1
  let rowId = 0

  let pendingDeletes = []
  let pendingInserts = []

  const flushPending = () => {
    const max = Math.max(pendingDeletes.length, pendingInserts.length)
    for (let i = 0; i < max; i += 1) {
      const leftText = pendingDeletes[i] ?? null
      const rightText = pendingInserts[i] ?? null

      if (leftText !== null && rightText !== null) {
        const segments = buildInlineSegments(leftText, rightText)
        result.push({
          key: `row-${rowId++}`,
          type: 'modify',
          leftLine: leftLine++,
          rightLine: rightLine++,
          leftText,
          rightText,
          leftSegments: segments.leftSegments,
          rightSegments: segments.rightSegments,
          leftClass: 'diff-cell--modify',
          rightClass: 'diff-cell--modify'
        })
      } else if (leftText !== null) {
        result.push({
          key: `row-${rowId++}`,
          type: 'delete',
          leftLine: leftLine++,
          rightLine: '',
          leftText,
          rightText: '',
          leftSegments: [{ type: 'delete', text: leftText }],
          rightSegments: [],
          leftClass: 'diff-cell--delete',
          rightClass: 'diff-cell--empty'
        })
      } else if (rightText !== null) {
        result.push({
          key: `row-${rowId++}`,
          type: 'insert',
          leftLine: '',
          rightLine: rightLine++,
          leftText: '',
          rightText,
          leftSegments: [],
          rightSegments: [{ type: 'insert', text: rightText }],
          leftClass: 'diff-cell--empty',
          rightClass: 'diff-cell--insert'
        })
      }
    }
    pendingDeletes = []
    pendingInserts = []
  }

  for (const [op, text] of diffs) {
    const lines = splitLines(text)
    if (lines.length === 0) continue

    if (op === DIFF_EQUAL) {
      flushPending()
      for (const line of lines) {
        result.push({
          key: `row-${rowId++}`,
          type: 'equal',
          leftLine: leftLine++,
          rightLine: rightLine++,
          leftText: line,
          rightText: line,
          leftClass: null,
          rightClass: null
        })
      }
    } else if (op === DIFF_DELETE) {
      pendingDeletes.push(...lines)
    } else if (op === DIFF_INSERT) {
      pendingInserts.push(...lines)
    }
  }

  flushPending()

  return result
})
</script>

<style scoped>
.diff-root {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 10px;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
}

.diff-header {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 8px 12px;
  background: rgba(var(--v-theme-surface-variant), 0.65);
  color: rgb(var(--v-theme-on-surface));
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.diff-header__side {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.diff-header__label {
  opacity: 0.7;
}

.diff-header__value {
  text-transform: none;
  letter-spacing: normal;
  font-weight: 600;
}

.diff-body {
  max-height: 320px;
  overflow: auto;
  background: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
}

.diff-empty {
  padding: 18px 12px;
  font-size: 13px;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.diff-rows {
  display: flex;
  flex-direction: column;
}

.diff-row {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr) 44px minmax(0, 1fr);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 12px;
  line-height: 1.5;
}

.diff-line {
  padding: 6px 8px;
  text-align: right;
  color: rgba(var(--v-theme-on-surface), 0.45);
  background: rgba(var(--v-theme-on-surface), 0.03);
  user-select: none;
}

.diff-cell {
  padding: 6px 10px;
  min-height: 24px;
  color: rgb(var(--v-theme-on-surface));
}

.diff-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.diff-cell--insert {
  background: rgba(var(--v-theme-success), 0.18);
  color: rgb(var(--v-theme-on-surface));
}

.diff-cell--delete {
  background: rgba(var(--v-theme-error), 0.18);
  color: rgb(var(--v-theme-on-surface));
}

.diff-cell--modify {
  background: rgba(var(--v-theme-info), 0.14);
  color: rgb(var(--v-theme-on-surface));
}

.diff-cell--empty {
  background: rgba(var(--v-theme-on-surface), 0.02);
}

.diff-inline {
  display: inline;
  white-space: pre-wrap;
}

.diff-inline--insert {
  background: rgba(var(--v-theme-success), 0.35);
  border-radius: 2px;
  padding: 0 1px;
}

.diff-inline--delete {
  background: rgba(var(--v-theme-error), 0.35);
  border-radius: 2px;
  padding: 0 1px;
}
</style>
