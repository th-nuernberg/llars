<template>
  <div class="l-agreement-heatmap">
    <div v-if="title" class="heatmap-title">{{ title }}</div>

    <div class="heatmap-container" v-if="sortedEvaluators.length > 1">
      <!-- Corner (empty) -->
      <div class="corner-cell"></div>

      <!-- X-axis labels (top) -->
      <div class="x-labels">
        <div
          v-for="evaluator in sortedEvaluators"
          :key="'x-' + evaluator.id"
          class="x-label"
          :class="{
            'is-llm': evaluator.isLLM,
            'highlighted': highlightedCell?.col === evaluator.id
          }"
          :title="getEvaluatorTooltip(evaluator)"
        >
          <LIcon v-if="evaluator.isLLM" size="10" class="llm-icon">mdi-robot</LIcon>
          <span>{{ getAxisLabel(evaluator, 'x') }}</span>
        </div>
      </div>

      <!-- Y-axis labels (left side) -->
      <div class="y-labels">
        <div
          v-for="evaluator in sortedEvaluators"
          :key="'y-' + evaluator.id"
          class="y-label"
          :class="{
            'is-llm': evaluator.isLLM,
            'highlighted': highlightedCell?.row === evaluator.id
          }"
          :title="getEvaluatorTooltip(evaluator)"
        >
          <LIcon v-if="evaluator.isLLM" size="12" class="mr-1">mdi-robot</LIcon>
          <span>{{ getAxisLabel(evaluator, 'y') }}</span>
        </div>
      </div>

      <!-- Cells grid -->
      <div class="cells-container">
        <div
          v-for="rowEval in sortedEvaluators"
          :key="'row-' + rowEval.id"
          class="heatmap-row"
        >
          <div
            v-for="colEval in sortedEvaluators"
            :key="rowEval.id + '-' + colEval.id"
            class="heatmap-cell"
            :class="{
              'diagonal': rowEval.id === colEval.id,
              'highlighted': highlightedCell?.row === rowEval.id && highlightedCell?.col === colEval.id,
              'clickable': rowEval.id !== colEval.id
            }"
            :style="getCellStyle(rowEval.id, colEval.id)"
            @mouseenter="onCellHover(rowEval, colEval)"
            @mouseleave="onCellLeave"
            @click="onCellClick(rowEval, colEval)"
          >
            <span v-if="showValues && rowEval.id !== colEval.id" class="cell-value">
              {{ formatValue(getAgreement(rowEval.id, colEval.id)) }}
            </span>
            <span v-else-if="rowEval.id === colEval.id" class="cell-value diagonal-marker">-</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <LIcon size="32" color="grey-lighten-1">mdi-account-multiple-outline</LIcon>
      <span>{{ emptyText || $t('scenarioManager.evaluation.needMoreEvaluators') }}</span>
    </div>

    <!-- Hover info - always visible to reserve space -->
    <div v-if="sortedEvaluators.length > 1 && showHoverInfo" class="hover-info">
      <template v-if="highlightedCell && highlightedCell.row !== highlightedCell.col">
        <div class="hover-evaluators">
          <span class="evaluator-name">{{ highlightedCell.rowName }}</span>
          <LIcon size="14" class="mx-1">mdi-arrow-left-right</LIcon>
          <span class="evaluator-name">{{ highlightedCell.colName }}</span>
        </div>
        <div class="hover-value">
          {{ $t('scenarioManager.evaluation.agreement') }}:
          <strong>{{ formatValue(highlightedCell.value) }}</strong>
        </div>
      </template>
      <template v-else>
        <div class="hover-placeholder">
          {{ $t('scenarioManager.evaluation.hoverForDetails') }}
        </div>
      </template>
    </div>

    <!-- Legend -->
    <div class="heatmap-legend" v-if="showLegend">
      <span class="legend-label">{{ lowLabel }}</span>
      <div class="legend-gradient"></div>
      <span class="legend-label">{{ highLabel }}</span>
    </div>

    <!-- Evaluator type legend -->
    <div class="evaluator-type-legend" v-if="showEvaluatorTypeLegend && hasLLMEvaluators">
      <div class="legend-item">
        <LIcon size="14">mdi-account</LIcon>
        <span>{{ $t('scenarioManager.evaluation.filter.human') }}</span>
      </div>
      <div class="legend-item llm">
        <LIcon size="14">mdi-robot</LIcon>
        <span>{{ $t('scenarioManager.evaluation.filter.llm') }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * LAgreementHeatmap - Global component for pairwise agreement visualization
 *
 * Displays a matrix showing how much each pair of evaluators agrees.
 * Values range from 0 (no agreement) to 1 (perfect agreement).
 * Uses LLARS Design System colors: red (low) -> yellow (medium) -> green (high).
 *
 * Usage:
 *   <LAgreementHeatmap
 *     :evaluators="[
 *       { id: 1, name: 'User A', isLLM: false },
 *       { id: 2, name: 'User B', isLLM: false },
 *       { id: 'gpt-4', name: 'GPT-4', isLLM: true }
 *     ]"
 *     :agreements="{
 *       '1-2': 0.85,
 *       '1-gpt-4': 0.72,
 *       '2-gpt-4': 0.78
 *     }"
 *     @cell-click="onCellClicked"
 *   />
 */
import { ref, computed } from 'vue'

const props = defineProps({
  /** List of evaluators with id, name, isLLM */
  evaluators: {
    type: Array,
    default: () => []
  },
  /** Pairwise agreement scores: { 'id1-id2': value } */
  agreements: {
    type: Object,
    default: () => ({})
  },
  /** Chart title */
  title: {
    type: String,
    default: ''
  },
  /** Show values in cells */
  showValues: {
    type: Boolean,
    default: true
  },
  /** Show hover info panel */
  showHoverInfo: {
    type: Boolean,
    default: true
  },
  /** Show color legend */
  showLegend: {
    type: Boolean,
    default: true
  },
  /** Show evaluator type legend (human/LLM) */
  showEvaluatorTypeLegend: {
    type: Boolean,
    default: true
  },
  /** Sort evaluators (humans first, then LLMs) */
  sortEvaluators: {
    type: Boolean,
    default: true
  },
  /** Label for low agreement */
  lowLabel: {
    type: String,
    default: '0%'
  },
  /** Label for high agreement */
  highLabel: {
    type: String,
    default: '100%'
  },
  /** Empty state text */
  emptyText: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['cell-click', 'cell-hover', 'cell-leave'])

const highlightedCell = ref(null)

// Sort evaluators: humans first, then LLMs (alphabetically within each group)
const sortedEvaluators = computed(() => {
  if (!props.sortEvaluators) return props.evaluators
  return [...props.evaluators].sort((a, b) => {
    if (a.isLLM === b.isLLM) return (a.name || '').localeCompare(b.name || '')
    return a.isLLM ? 1 : -1
  })
})

const hasLLMEvaluators = computed(() => {
  return props.evaluators.some(e => e.isLLM)
})

function truncateMiddle(text, maxLength) {
  const value = String(text || '')
  if (value.length <= maxLength) return value
  const visible = maxLength - 3
  const head = Math.ceil(visible / 2)
  const tail = Math.floor(visible / 2)
  return `${value.slice(0, head)}...${value.slice(-tail)}`
}

function normalizeEvaluatorName(evaluator) {
  if (!evaluator) return '?'
  const fallback = evaluator.name || evaluator.model_name || evaluator.username || evaluator.id || '?'
  const raw = String(fallback).replace(/^llm:/, '')

  if (!evaluator.isLLM) {
    return raw
  }

  // Prefer readable model names (e.g. provider/model-name -> model-name)
  const modelPart = raw.includes('/') ? raw.split('/').pop() : raw
  return modelPart || raw
}

function getAxisLabel(evaluator, axis = 'y') {
  const normalized = normalizeEvaluatorName(evaluator)
  const maxLength = axis === 'x' ? 18 : 30
  return truncateMiddle(normalized, maxLength)
}

function getEvaluatorTooltip(evaluator) {
  const displayName = normalizeEvaluatorName(evaluator)
  const rawId = evaluator?.id ? String(evaluator.id).replace(/^llm:/, '') : ''
  if (evaluator?.isLLM && rawId && rawId !== displayName) {
    return `${displayName} (${rawId})`
  }
  return displayName
}

function getAgreementKey(id1, id2) {
  // Normalize key order for symmetric lookup
  const str1 = String(id1)
  const str2 = String(id2)
  return str1 < str2 ? `${str1}-${str2}` : `${str2}-${str1}`
}

function getAgreement(id1, id2) {
  if (id1 === id2) return 1
  const key = getAgreementKey(id1, id2)
  return props.agreements[key] ?? null
}

function formatValue(value) {
  if (value === null || value === undefined) return '-'
  return Math.round(value * 100) + '%'
}

const HEATMAP_COLOR_STOPS = [
  { value: 0, color: { r: 210, g: 99, b: 79 } },   // low: deeper coral
  { value: 0.5, color: { r: 209, g: 188, b: 138 } }, // mid: LLARS beige
  { value: 1, color: { r: 86, g: 165, b: 137 } }     // high: deeper mint
]

function interpolateColor(start, end, t) {
  return {
    r: Math.round(start.r + (end.r - start.r) * t),
    g: Math.round(start.g + (end.g - start.g) * t),
    b: Math.round(start.b + (end.b - start.b) * t)
  }
}

function getInterpolatedHeatmapColor(intensity) {
  if (intensity <= HEATMAP_COLOR_STOPS[0].value) return HEATMAP_COLOR_STOPS[0].color
  if (intensity >= HEATMAP_COLOR_STOPS[HEATMAP_COLOR_STOPS.length - 1].value) {
    return HEATMAP_COLOR_STOPS[HEATMAP_COLOR_STOPS.length - 1].color
  }

  for (let i = 0; i < HEATMAP_COLOR_STOPS.length - 1; i++) {
    const start = HEATMAP_COLOR_STOPS[i]
    const end = HEATMAP_COLOR_STOPS[i + 1]
    if (intensity >= start.value && intensity <= end.value) {
      const t = (intensity - start.value) / (end.value - start.value)
      return interpolateColor(start.color, end.color, t)
    }
  }

  return HEATMAP_COLOR_STOPS[1].color
}

function getReadableTextColor({ r, g, b }) {
  // YIQ contrast check for readable foreground on varying backgrounds
  const yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000
  return yiq >= 150 ? 'rgba(var(--v-theme-on-surface), 0.92)' : 'rgba(255, 255, 255, 0.96)'
}

function getCellStyle(rowId, colId) {
  if (rowId === colId) {
    return {
      backgroundColor: 'rgba(var(--v-theme-on-surface), 0.05)'
    }
  }

  const value = getAgreement(rowId, colId)
  if (value === null) {
    return {
      backgroundColor: 'rgba(var(--v-theme-surface-variant), 0.5)'
    }
  }

  // Stronger gradient for clearer agreement differences:
  // low (deeper coral) -> medium (beige) -> high (deeper mint)
  const intensity = Math.max(0, Math.min(1, value))
  const { r, g, b } = getInterpolatedHeatmapColor(intensity)

  return {
    backgroundColor: `rgb(${r}, ${g}, ${b})`,
    color: getReadableTextColor({ r, g, b })
  }
}

function onCellHover(rowEval, colEval) {
  highlightedCell.value = {
    row: rowEval.id,
    col: colEval.id,
    rowName: getEvaluatorTooltip(rowEval),
    colName: getEvaluatorTooltip(colEval),
    value: getAgreement(rowEval.id, colEval.id)
  }
  emit('cell-hover', {
    evaluator1: rowEval,
    evaluator2: colEval,
    value: getAgreement(rowEval.id, colEval.id)
  })
}

function onCellLeave() {
  highlightedCell.value = null
  emit('cell-leave')
}

function onCellClick(rowEval, colEval) {
  if (rowEval.id === colEval.id) return
  emit('cell-click', {
    evaluator1: rowEval,
    evaluator2: colEval,
    value: getAgreement(rowEval.id, colEval.id),
    percentage: Math.round((getAgreement(rowEval.id, colEval.id) || 0) * 100)
  })
}
</script>

<style scoped>
.l-agreement-heatmap {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background-color: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 12px;
  min-height: 280px;
}

.heatmap-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin-bottom: 16px;
  text-align: center;
}

.heatmap-container {
  display: grid;
  grid-template-columns: minmax(120px, auto) auto;
  grid-template-rows: auto auto;
  justify-content: center;
  align-content: center;
  flex: 1;
  width: 100%;
  gap: 0;
}

.y-labels {
  display: flex;
  flex-direction: column;
  grid-column: 1;
  grid-row: 2;
  justify-self: end;
}

.corner-cell {
  grid-column: 1;
  grid-row: 1;
  min-width: 120px;
  height: 90px;
}

.y-label {
  height: 60px;
  max-width: 220px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 10px;
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: background-color 0.15s;
  box-sizing: border-box;
}

.y-label.is-llm {
  color: rgb(var(--v-theme-accent));
}

.y-label.highlighted {
  background-color: rgba(var(--v-theme-primary), 0.1);
  border-radius: 4px;
}

.x-labels {
  display: flex;
  grid-column: 2;
  grid-row: 1;
  height: 90px;
  align-items: flex-end;
}

.x-label {
  width: 60px;
  height: 90px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  writing-mode: vertical-rl;
  transform: rotate(180deg);
  font-size: 0.75rem;
  font-weight: 500;
  padding-bottom: 8px;
  transition: background-color 0.15s;
  box-sizing: border-box;
}

.x-label .llm-icon {
  margin-bottom: 2px;
}

.x-label.is-llm {
  color: rgb(var(--v-theme-accent));
}

.x-label.highlighted {
  background-color: rgba(var(--v-theme-primary), 0.1);
  border-radius: 4px;
}

.cells-container {
  display: flex;
  flex-direction: column;
  grid-column: 2;
  grid-row: 2;
}

.heatmap-row {
  display: flex;
  height: 60px;
}

.heatmap-cell {
  width: 60px;
  height: 60px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  cursor: default;
  transition: box-shadow 0.15s, outline 0.15s;
  border-radius: 4px;
  box-sizing: border-box;
}

.heatmap-cell.clickable {
  cursor: pointer;
}

/* Subtle hover: no size change, just highlight */
.heatmap-cell.clickable:hover {
  box-shadow: inset 0 0 0 2px rgba(255, 255, 255, 0.4);
}

.heatmap-cell.highlighted {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: -1px;
}

.cell-value {
  font-size: 0.85rem;
  font-weight: 600;
}

.diagonal-marker {
  color: rgba(var(--v-theme-on-surface), 0.3);
  font-size: 1.1rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 0.8rem;
  flex: 1;
  min-height: 200px;
}

/* Reserved space for hover info - fixed size prevents layout shift */
.hover-info {
  margin-top: 16px;
  padding: 12px 20px;
  background-color: rgba(var(--v-theme-surface), 0.9);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 10px;
  text-align: center;
  /* Fixed dimensions to prevent any layout shift */
  height: 56px;
  width: min(90%, 300px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.hover-evaluators {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: 500;
  margin-bottom: 2px;
  line-height: 1.2;
}

.evaluator-name {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hover-value {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  line-height: 1.2;
}

.hover-placeholder {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.4);
  line-height: 1.2;
}

.heatmap-legend {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 16px;
  gap: 10px;
}

.legend-gradient {
  width: 100px;
  height: 10px;
  background: linear-gradient(to right, #d2634f, #D1BC8A, #56a589);
  border-radius: 4px;
}

.legend-label {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Evaluator type legend */
.evaluator-type-legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.evaluator-type-legend .legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.evaluator-type-legend .legend-item.llm {
  color: rgb(var(--v-theme-accent));
}

/* Responsive */
@media (max-width: 600px) {
  .l-agreement-heatmap {
    padding: 12px;
  }

  .heatmap-container {
    grid-template-columns: minmax(90px, auto) auto;
  }

  .y-label, .x-label {
    font-size: 0.65rem;
  }

  .heatmap-cell, .y-label, .heatmap-row, .x-label {
    width: 48px;
    height: 48px;
  }

  .x-label {
    height: 64px;
  }

  .corner-cell {
    min-width: 90px;
    height: 64px;
  }

  .y-label {
    max-width: 150px;
  }

  .cell-value {
    font-size: 0.7rem;
  }
}
</style>
