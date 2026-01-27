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
          :title="evaluator.name"
        >
          <LIcon v-if="evaluator.isLLM" size="10" class="llm-icon">mdi-robot</LIcon>
          <span>{{ getShortName(evaluator.name) }}</span>
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
          :title="evaluator.name"
        >
          <LIcon v-if="evaluator.isLLM" size="12" class="mr-1">mdi-robot</LIcon>
          <span>{{ getShortName(evaluator.name) }}</span>
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

function getShortName(name) {
  if (!name) return '?'
  // For LLM model names, extract the model part
  if (name.includes('/')) {
    name = name.split('/').pop()
  }
  if (name.length <= 8) return name
  return name.substring(0, 7) + '...'
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

  // Color gradient using LLARS Design System colors:
  // low (red #e8a087) -> medium (yellow #D1BC8A) -> high (green #98d4bb)
  const intensity = Math.max(0, Math.min(1, value))

  let r, g, b
  if (intensity < 0.5) {
    // Red to yellow
    const t = intensity * 2
    r = 232 // e8
    g = Math.round(160 + t * 40) // a0 -> c8
    b = Math.round(135 - t * 35) // 87 -> 52
  } else {
    // Yellow to green
    const t = (intensity - 0.5) * 2
    r = Math.round(232 - t * 80) // e8 -> 98
    g = Math.round(200 + t * 12) // c8 -> d4
    b = Math.round(100 + t * 87) // 64 -> bb
  }

  return {
    backgroundColor: `rgb(${r}, ${g}, ${b})`,
    color: intensity > 0.6 ? 'white' : 'inherit'
  }
}

function onCellHover(rowEval, colEval) {
  highlightedCell.value = {
    row: rowEval.id,
    col: colEval.id,
    rowName: rowEval.name,
    colName: colEval.name,
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
  grid-template-columns: minmax(60px, auto) auto;
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
  min-width: 60px;
  height: 80px;
}

.y-label {
  height: 56px;
  max-width: 120px;
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
  height: 80px;
  align-items: flex-end;
}

.x-label {
  width: 56px;
  height: 80px;
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
  height: 56px;
}

.heatmap-cell {
  width: 56px;
  height: 56px;
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
  background: linear-gradient(to right, #e8a087, #D1BC8A, #98d4bb);
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

  .y-label, .x-label {
    font-size: 0.65rem;
  }

  .heatmap-cell, .y-label, .heatmap-row, .x-label {
    width: 44px;
    height: 44px;
  }

  .x-label {
    height: 60px;
  }

  .corner-cell {
    height: 60px;
  }

  .cell-value {
    font-size: 0.7rem;
  }
}
</style>
