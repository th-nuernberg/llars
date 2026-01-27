<template>
  <div class="l-confusion-matrix" :class="[`size-${size}`]">
    <!-- Matrix Header -->
    <div class="matrix-header">
      <h4 class="matrix-title">
        <LIcon start :size="size === 'compact' ? 16 : 20">mdi-grid</LIcon>
        {{ title || $t('scenarioManager.results.confusionMatrix.title') }}
      </h4>
      <div class="matrix-controls" v-if="showControls">
        <v-btn-toggle v-model="displayMode" density="compact" variant="outlined" divided>
          <v-btn value="counts" size="x-small">
            <LIcon start :size="size === 'compact' ? 12 : 16">mdi-numeric</LIcon>
            {{ $t('scenarioManager.results.confusionMatrix.counts') }}
          </v-btn>
          <v-btn value="percentages" size="x-small">
            <LIcon start :size="size === 'compact' ? 12 : 16">mdi-percent</LIcon>
            {{ $t('scenarioManager.results.confusionMatrix.percentages') }}
          </v-btn>
        </v-btn-toggle>
      </div>
    </div>

    <!-- Matrix Grid -->
    <div class="matrix-wrapper">
      <!-- Y-Axis Label -->
      <div class="axis-label y-axis">
        <span>{{ yAxisLabel || $t('scenarioManager.results.confusionMatrix.predicted') }}</span>
      </div>

      <div class="matrix-content">
        <!-- Matrix Table -->
        <div class="matrix-table" :style="{ '--cols': columns.length + 1 }">
          <!-- X-Axis Label Row -->
          <div class="matrix-row axis-row">
            <div class="matrix-cell corner-cell axis-spacer"></div>
            <div class="axis-label x-axis">
              <span>{{ xAxisLabel || $t('scenarioManager.results.confusionMatrix.actual') }}</span>
            </div>
          </div>

          <!-- Header Row -->
          <div class="matrix-row header-row">
            <div class="matrix-cell corner-cell"></div>
            <div
              v-for="(col, index) in columns"
              :key="'col-' + index"
              class="matrix-cell header-cell"
              :style="{ color: col.color || getDefaultHeaderColor(index) }"
            >
              <LIcon v-if="col.icon" :size="size === 'compact' ? 12 : 16" class="mr-1">{{ col.icon }}</LIcon>
              {{ col.label }}
            </div>
            <div class="matrix-cell header-cell totals">
              {{ $t('scenarioManager.results.confusionMatrix.total') }}
            </div>
          </div>

          <!-- Data Rows -->
          <div
            v-for="(row, rowIndex) in rows"
            :key="'row-' + rowIndex"
            class="matrix-row"
          >
            <div
              class="matrix-cell row-header"
              :style="{ color: row.color || getDefaultHeaderColor(rowIndex) }"
            >
              <LIcon v-if="row.icon" :size="size === 'compact' ? 12 : 16" class="mr-1">{{ row.icon }}</LIcon>
              {{ row.label }}
            </div>
            <div
              v-for="(col, colIndex) in columns"
              :key="'cell-' + rowIndex + '-' + colIndex"
              class="matrix-cell value-cell"
              :class="getCellClass(rowIndex, colIndex)"
              :style="getCellStyle(rowIndex, colIndex)"
              @click="$emit('cell-click', { row: rowIndex, col: colIndex, value: getMatrixValue(rowIndex, colIndex) })"
            >
              <span class="cell-value">{{ formatValue(getMatrixValue(rowIndex, colIndex)) }}</span>
              <span class="cell-label" v-if="showCellLabels">{{ getCellLabel(rowIndex, colIndex) }}</span>
            </div>
            <div class="matrix-cell total-cell">
              {{ getRowTotal(rowIndex) }}
            </div>
          </div>

          <!-- Totals Row -->
          <div class="matrix-row totals-row">
            <div class="matrix-cell row-header">
              {{ $t('scenarioManager.results.confusionMatrix.total') }}
            </div>
            <div
              v-for="(col, colIndex) in columns"
              :key="'total-' + colIndex"
              class="matrix-cell total-cell"
            >
              {{ getColumnTotal(colIndex) }}
            </div>
            <div class="matrix-cell total-cell grand-total">
              {{ totalCount }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Metrics Summary -->
    <div class="metrics-summary" v-if="showMetrics && isBinaryMatrix">
      <div class="metric-item">
        <span class="metric-label">{{ $t('scenarioManager.results.confusionMatrix.accuracy') }}</span>
        <span class="metric-value" :class="getMetricClass(metrics.accuracy)">
          {{ metrics.accuracy !== null ? metrics.accuracy.toFixed(1) + '%' : '-' }}
        </span>
      </div>
      <div class="metric-item">
        <span class="metric-label">{{ $t('scenarioManager.results.confusionMatrix.precision') }}</span>
        <span class="metric-value" :class="getMetricClass(metrics.precision)">
          {{ metrics.precision !== null ? metrics.precision.toFixed(1) + '%' : '-' }}
        </span>
        <LTooltip :text="$t('scenarioManager.results.confusionMatrix.precisionTooltip')">
          <LIcon :size="size === 'compact' ? 12 : 14" class="info-icon">mdi-information-outline</LIcon>
        </LTooltip>
      </div>
      <div class="metric-item">
        <span class="metric-label">{{ $t('scenarioManager.results.confusionMatrix.recall') }}</span>
        <span class="metric-value" :class="getMetricClass(metrics.recall)">
          {{ metrics.recall !== null ? metrics.recall.toFixed(1) + '%' : '-' }}
        </span>
        <LTooltip :text="$t('scenarioManager.results.confusionMatrix.recallTooltip')">
          <LIcon :size="size === 'compact' ? 12 : 14" class="info-icon">mdi-information-outline</LIcon>
        </LTooltip>
      </div>
      <div class="metric-item">
        <span class="metric-label">{{ $t('scenarioManager.results.confusionMatrix.f1Score') }}</span>
        <span class="metric-value" :class="getMetricClass(metrics.f1)">
          {{ metrics.f1 !== null ? metrics.f1.toFixed(2) : '-' }}
        </span>
        <LTooltip :text="$t('scenarioManager.results.confusionMatrix.f1Tooltip')">
          <LIcon :size="size === 'compact' ? 12 : 14" class="info-icon">mdi-information-outline</LIcon>
        </LTooltip>
      </div>
    </div>

    <!-- Legend -->
    <div class="matrix-legend" v-if="showLegend && isBinaryMatrix">
      <div class="legend-item">
        <span class="legend-color tp"></span>
        <span class="legend-text">
          <strong>TP</strong> - {{ $t('scenarioManager.results.confusionMatrix.tpDescription') }}
        </span>
      </div>
      <div class="legend-item">
        <span class="legend-color fp"></span>
        <span class="legend-text">
          <strong>FP</strong> - {{ $t('scenarioManager.results.confusionMatrix.fpDescription') }}
        </span>
      </div>
      <div class="legend-item">
        <span class="legend-color fn"></span>
        <span class="legend-text">
          <strong>FN</strong> - {{ $t('scenarioManager.results.confusionMatrix.fnDescription') }}
        </span>
      </div>
      <div class="legend-item">
        <span class="legend-color tn"></span>
        <span class="legend-text">
          <strong>TN</strong> - {{ $t('scenarioManager.results.confusionMatrix.tnDescription') }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * LConfusionMatrix - Global confusion matrix / heatmap component
 *
 * Supports both binary classification (TP/FP/TN/FN) and multi-class matrices.
 * Responsive with size variants: 'default', 'compact', 'large'.
 *
 * Usage (Binary - Authenticity):
 *   <LConfusionMatrix
 *     :matrix="{ truePositive: 20, falsePositive: 4, trueNegative: 18, falseNegative: 2 }"
 *     :labels="{ actualFake: 'Tats. Fake', predictedFake: 'Vorh. Fake' }"
 *   />
 *
 * Usage (Multi-class):
 *   <LConfusionMatrix
 *     :rows="[{ label: 'Cat A', icon: 'mdi-tag' }, { label: 'Cat B' }]"
 *     :columns="[{ label: 'Cat A' }, { label: 'Cat B' }]"
 *     :data="[[10, 2], [3, 15]]"
 *     size="compact"
 *   />
 */
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  /**
   * Binary confusion matrix data (for authenticity scenarios)
   * { truePositive, falsePositive, trueNegative, falseNegative }
   */
  matrix: {
    type: Object,
    default: null
  },
  /**
   * Multi-class matrix data (2D array)
   */
  data: {
    type: Array,
    default: null
  },
  /**
   * Row definitions for multi-class matrix
   * [{ label: string, icon?: string, color?: string }]
   */
  rows: {
    type: Array,
    default: null
  },
  /**
   * Column definitions for multi-class matrix
   * [{ label: string, icon?: string, color?: string }]
   */
  columns: {
    type: Array,
    default: null
  },
  /**
   * Custom title
   */
  title: {
    type: String,
    default: ''
  },
  /**
   * Custom labels for binary matrix
   */
  labels: {
    type: Object,
    default: () => ({})
  },
  /**
   * Custom axis labels
   */
  xAxisLabel: {
    type: String,
    default: ''
  },
  yAxisLabel: {
    type: String,
    default: ''
  },
  /**
   * Size variant: 'compact', 'default', 'large'
   */
  size: {
    type: String,
    default: 'default',
    validator: (v) => ['compact', 'default', 'large'].includes(v)
  },
  /**
   * Show toggle between counts and percentages
   */
  showControls: {
    type: Boolean,
    default: true
  },
  /**
   * Show metrics summary (accuracy, precision, recall, F1) - only for binary
   */
  showMetrics: {
    type: Boolean,
    default: true
  },
  /**
   * Show legend explaining TP, FP, TN, FN - only for binary
   */
  showLegend: {
    type: Boolean,
    default: false
  },
  /**
   * Show cell labels (TP, FP, etc.) in cells
   */
  showCellLabels: {
    type: Boolean,
    default: true
  },
  /**
   * Use heatmap coloring based on values
   */
  useHeatmap: {
    type: Boolean,
    default: true
  },
  /**
   * Custom color for correct predictions (diagonal)
   */
  correctColor: {
    type: String,
    default: 'rgba(152, 212, 187, 0.6)'
  },
  /**
   * Custom color for incorrect predictions (off-diagonal)
   */
  incorrectColor: {
    type: String,
    default: 'rgba(232, 160, 135, 0.6)'
  }
})

const emit = defineEmits(['cell-click'])

const { t } = useI18n()

// State
const displayMode = ref('counts')

// Computed: Determine if binary or multi-class matrix
const isBinaryMatrix = computed(() => {
  return props.matrix !== null && !props.data
})

// Computed: Normalized rows/columns for both binary and multi-class
const normalizedRows = computed(() => {
  if (props.rows) return props.rows
  if (isBinaryMatrix.value) {
    return [
      {
        label: props.labels.predictedFake || t('scenarioManager.results.confusionMatrix.predictedFake'),
        icon: 'mdi-robot-angry-outline',
        color: '#e8a087'
      },
      {
        label: props.labels.predictedReal || t('scenarioManager.results.confusionMatrix.predictedReal'),
        icon: 'mdi-account-check-outline',
        color: '#98d4bb'
      }
    ]
  }
  return []
})

const normalizedColumns = computed(() => {
  if (props.columns) return props.columns
  if (isBinaryMatrix.value) {
    return [
      {
        label: props.labels.actualFake || t('scenarioManager.results.confusionMatrix.actualFake'),
        icon: 'mdi-robot-angry-outline',
        color: '#e8a087'
      },
      {
        label: props.labels.actualReal || t('scenarioManager.results.confusionMatrix.actualReal'),
        icon: 'mdi-account-check-outline',
        color: '#98d4bb'
      }
    ]
  }
  return []
})

const rows = computed(() => normalizedRows.value)
const columns = computed(() => normalizedColumns.value)

// Computed: Normalized matrix data
const matrixData = computed(() => {
  if (props.data) return props.data
  if (isBinaryMatrix.value) {
    const m = props.matrix
    return [
      [m.truePositive || 0, m.falsePositive || 0],
      [m.falseNegative || 0, m.trueNegative || 0]
    ]
  }
  return []
})

// Computed: Totals
const totalCount = computed(() => {
  let sum = 0
  for (const row of matrixData.value) {
    for (const val of row) {
      sum += val || 0
    }
  }
  return sum
})

// Computed: Metrics (only for binary)
const metrics = computed(() => {
  if (!isBinaryMatrix.value) {
    return { accuracy: null, precision: null, recall: null, f1: null }
  }

  const m = props.matrix
  const total = totalCount.value

  if (total === 0) {
    return { accuracy: null, precision: null, recall: null, f1: null }
  }

  const tp = m.truePositive || 0
  const fp = m.falsePositive || 0
  const tn = m.trueNegative || 0
  const fn = m.falseNegative || 0

  // Accuracy = (TP + TN) / Total
  const accuracy = ((tp + tn) / total) * 100

  // Precision = TP / (TP + FP)
  const precision = (tp + fp) > 0
    ? (tp / (tp + fp)) * 100
    : null

  // Recall = TP / (TP + FN)
  const recall = (tp + fn) > 0
    ? (tp / (tp + fn)) * 100
    : null

  // F1 Score = 2 * (Precision * Recall) / (Precision + Recall)
  const f1 = (precision !== null && recall !== null && (precision + recall) > 0)
    ? (2 * (precision / 100) * (recall / 100)) / ((precision / 100) + (recall / 100))
    : null

  return { accuracy, precision, recall, f1 }
})

// Methods
function getMatrixValue(rowIndex, colIndex) {
  if (!matrixData.value[rowIndex]) return 0
  return matrixData.value[rowIndex][colIndex] || 0
}

function getRowTotal(rowIndex) {
  if (!matrixData.value[rowIndex]) return 0
  return matrixData.value[rowIndex].reduce((sum, val) => sum + (val || 0), 0)
}

function getColumnTotal(colIndex) {
  return matrixData.value.reduce((sum, row) => sum + (row[colIndex] || 0), 0)
}

function formatValue(value) {
  if (displayMode.value === 'percentages') {
    const total = totalCount.value
    if (total === 0) return '0%'
    return ((value / total) * 100).toFixed(1) + '%'
  }
  return value
}

function getCellLabel(rowIndex, colIndex) {
  if (!isBinaryMatrix.value) return ''
  const labels = [['TP', 'FP'], ['FN', 'TN']]
  return labels[rowIndex]?.[colIndex] || ''
}

function getCellClass(rowIndex, colIndex) {
  const classes = []
  if (isBinaryMatrix.value) {
    const cellTypes = [['tp', 'fp'], ['fn', 'tn']]
    classes.push(cellTypes[rowIndex]?.[colIndex] || '')
  }
  if (props.useHeatmap) {
    classes.push('heatmap')
  }
  // Diagonal = correct prediction
  if (rowIndex === colIndex) {
    classes.push('correct')
  } else {
    classes.push('incorrect')
  }
  return classes
}

function getCellStyle(rowIndex, colIndex) {
  if (!props.useHeatmap) return {}

  const total = totalCount.value
  if (total === 0) return {}

  const value = getMatrixValue(rowIndex, colIndex)
  const intensity = Math.min(value / total, 1)

  // Correct predictions (diagonal) - green tint
  // Incorrect predictions (off-diagonal) - red tint
  if (rowIndex === colIndex) {
    return {
      backgroundColor: `rgba(152, 212, 187, ${0.15 + intensity * 0.6})`
    }
  } else {
    return {
      backgroundColor: `rgba(232, 160, 135, ${0.15 + intensity * 0.6})`
    }
  }
}

function getMetricClass(value) {
  if (value === null) return ''
  if (value >= 80) return 'excellent'
  if (value >= 60) return 'good'
  if (value >= 40) return 'moderate'
  return 'poor'
}

function getDefaultHeaderColor(index) {
  const colors = ['#e8a087', '#98d4bb', '#88c4c8', '#D1BC8A']
  return colors[index % colors.length]
}
</script>

<style scoped>
.l-confusion-matrix {
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
  padding: 20px;
}

/* Size variants */
.l-confusion-matrix.size-compact {
  padding: 12px;
}

.l-confusion-matrix.size-compact .matrix-title {
  font-size: 0.85rem;
}

.l-confusion-matrix.size-compact .matrix-cell {
  min-width: 60px;
  min-height: 44px;
  padding: 4px 6px;
  font-size: 0.75rem;
}

.l-confusion-matrix.size-compact .cell-value {
  font-size: 1rem;
}

.l-confusion-matrix.size-compact .cell-label {
  font-size: 0.55rem;
}

.l-confusion-matrix.size-compact .row-header {
  /* Let grid handle width - row-header column uses max-content */
}

.l-confusion-matrix.size-compact .axis-label {
  font-size: 0.65rem;
}

.l-confusion-matrix.size-compact .metric-item {
  padding: 4px 10px;
}

.l-confusion-matrix.size-compact .metric-label {
  font-size: 0.7rem;
}

.l-confusion-matrix.size-compact .metric-value {
  font-size: 0.85rem;
}

.l-confusion-matrix.size-large .matrix-cell {
  min-width: 120px;
  min-height: 80px;
}

.l-confusion-matrix.size-large .cell-value {
  font-size: 1.5rem;
}

/* Header */
.matrix-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.matrix-title {
  display: flex;
  align-items: center;
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

/* Matrix Wrapper */
.matrix-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.axis-label {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.axis-label.y-axis {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  transform: rotate(180deg);
  padding-right: 8px;
  margin-top: 28px; /* Offset for x-axis label + header row */
  margin-bottom: auto; /* Don't extend to totals row */
}

.axis-label.x-axis {
  grid-column: 2 / -1; /* Span from 2nd column to last */
  padding-bottom: 4px;
  text-align: center;
  min-height: 24px;
}

.matrix-row.axis-row .axis-spacer {
  min-height: 24px;
  height: 24px;
}

.matrix-content {
  display: flex;
  flex-direction: column;
}

.matrix-table {
  display: grid;
  /* First column auto-sizes to widest row header, rest are equal 1fr columns */
  grid-template-columns: max-content repeat(var(--cols, 3), minmax(70px, 1fr));
  gap: 2px;
}

.matrix-row {
  display: contents; /* Children participate directly in grid */
}

.matrix-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 56px;
  min-width: 0; /* Prevent grid items from overflowing */
  padding: 6px 10px;
  font-size: 0.8rem;
}

.corner-cell {
  background: transparent;
  min-width: 0;
}

.header-cell {
  background-color: rgba(var(--v-theme-on-surface), 0.04);
  font-weight: 600;
  border-radius: 6px 6px 0 0;
}

.row-header {
  background-color: rgba(var(--v-theme-on-surface), 0.04);
  font-weight: 600;
  justify-content: flex-start;
  border-radius: 6px 0 0 6px;
  white-space: nowrap;
  padding: 6px 12px;
}

.value-cell {
  flex-direction: column;
  gap: 2px;
  border-radius: 4px;
  transition: background-color 0.2s, transform 0.15s;
  cursor: pointer;
}

.value-cell:hover {
  transform: scale(1.05);
}

.cell-value {
  font-size: 1.25rem;
  font-weight: 700;
}

.cell-label {
  font-size: 0.6rem;
  font-weight: 600;
  text-transform: uppercase;
  opacity: 0.6;
}

.value-cell.correct .cell-value {
  color: #2e7d32;
}

.value-cell.incorrect .cell-value {
  color: #c62828;
}

.total-cell {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.grand-total {
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
}

.totals-row .row-header {
  font-size: 0.7rem;
  text-transform: uppercase;
}

/* Metrics Summary */
.metrics-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px;
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  margin-bottom: 12px;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background-color: rgb(var(--v-theme-surface));
  border-radius: 6px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.metric-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.metric-value {
  font-size: 0.9rem;
  font-weight: 600;
}

.metric-value.excellent { color: #4caf50; }
.metric-value.good { color: #8bc34a; }
.metric-value.moderate { color: #ff9800; }
.metric-value.poor { color: #f44336; }

.info-icon {
  color: rgba(var(--v-theme-on-surface), 0.4);
  cursor: help;
}

/* Legend */
.matrix-legend {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.legend-color {
  width: 14px;
  height: 14px;
  border-radius: 4px;
}

.legend-color.tp { background-color: rgba(152, 212, 187, 0.6); }
.legend-color.tn { background-color: rgba(152, 212, 187, 0.4); }
.legend-color.fp { background-color: rgba(232, 160, 135, 0.6); }
.legend-color.fn { background-color: rgba(232, 160, 135, 0.4); }

.legend-text strong {
  color: rgb(var(--v-theme-on-surface));
}

/* Responsive */
@media (max-width: 600px) {
  .l-confusion-matrix {
    padding: 12px;
  }

  .matrix-cell {
    min-width: 56px;
    min-height: 44px;
    padding: 4px 6px;
    font-size: 0.7rem;
  }

  .cell-value {
    font-size: 0.9rem;
  }

  .row-header {
    /* Let grid handle width - row-header column uses max-content */
  }

  .metrics-summary {
    flex-direction: column;
  }

  .matrix-legend {
    grid-template-columns: 1fr;
  }

  .axis-label.y-axis {
    display: none;
  }

  .matrix-row.axis-row .axis-spacer {
    /* Let grid handle width - row-header column uses max-content */
  }
}
</style>
