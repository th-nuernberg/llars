<template>
  <div class="confusion-matrix-container">
    <!-- Matrix Header -->
    <div class="matrix-header">
      <h4 class="matrix-title">
        <LIcon start size="20">mdi-grid</LIcon>
        {{ title || $t('scenarioManager.results.confusionMatrix.title') }}
      </h4>
      <div class="matrix-controls" v-if="showControls">
        <v-btn-toggle v-model="displayMode" density="compact" variant="outlined" divided>
          <v-btn value="counts" size="small">
            <LIcon start size="16">mdi-numeric</LIcon>
            {{ $t('scenarioManager.results.confusionMatrix.counts') }}
          </v-btn>
          <v-btn value="percentages" size="small">
            <LIcon start size="16">mdi-percent</LIcon>
            {{ $t('scenarioManager.results.confusionMatrix.percentages') }}
          </v-btn>
        </v-btn-toggle>
      </div>
    </div>

    <!-- Matrix Grid -->
    <div class="matrix-wrapper">
      <!-- Y-Axis Label -->
      <div class="axis-label y-axis">
        <span>{{ $t('scenarioManager.results.confusionMatrix.predicted') }}</span>
      </div>

      <div class="matrix-content">
        <!-- X-Axis Label -->
        <div class="axis-label x-axis">
          <span>{{ $t('scenarioManager.results.confusionMatrix.actual') }}</span>
        </div>

        <!-- Matrix Table -->
        <div class="matrix-table">
          <!-- Header Row -->
          <div class="matrix-row header-row">
            <div class="matrix-cell corner-cell"></div>
            <div class="matrix-cell header-cell actual-fake">
              <LIcon size="16" class="mr-1">mdi-robot-angry-outline</LIcon>
              {{ labels.actualFake || $t('scenarioManager.results.confusionMatrix.actualFake') }}
            </div>
            <div class="matrix-cell header-cell actual-real">
              <LIcon size="16" class="mr-1">mdi-account-check-outline</LIcon>
              {{ labels.actualReal || $t('scenarioManager.results.confusionMatrix.actualReal') }}
            </div>
            <div class="matrix-cell header-cell totals">
              {{ $t('scenarioManager.results.confusionMatrix.total') }}
            </div>
          </div>

          <!-- Predicted Fake Row -->
          <div class="matrix-row">
            <div class="matrix-cell row-header predicted-fake">
              <LIcon size="16" class="mr-1">mdi-robot-angry-outline</LIcon>
              {{ labels.predictedFake || $t('scenarioManager.results.confusionMatrix.predictedFake') }}
            </div>
            <div
              class="matrix-cell value-cell tp"
              :class="getCellClass('tp')"
              :style="getCellStyle('tp')"
            >
              <span class="cell-value">{{ formatValue(matrix.truePositive) }}</span>
              <span class="cell-label">TP</span>
            </div>
            <div
              class="matrix-cell value-cell fp"
              :class="getCellClass('fp')"
              :style="getCellStyle('fp')"
            >
              <span class="cell-value">{{ formatValue(matrix.falsePositive) }}</span>
              <span class="cell-label">FP</span>
            </div>
            <div class="matrix-cell total-cell">
              {{ matrix.truePositive + matrix.falsePositive }}
            </div>
          </div>

          <!-- Predicted Real Row -->
          <div class="matrix-row">
            <div class="matrix-cell row-header predicted-real">
              <LIcon size="16" class="mr-1">mdi-account-check-outline</LIcon>
              {{ labels.predictedReal || $t('scenarioManager.results.confusionMatrix.predictedReal') }}
            </div>
            <div
              class="matrix-cell value-cell fn"
              :class="getCellClass('fn')"
              :style="getCellStyle('fn')"
            >
              <span class="cell-value">{{ formatValue(matrix.falseNegative) }}</span>
              <span class="cell-label">FN</span>
            </div>
            <div
              class="matrix-cell value-cell tn"
              :class="getCellClass('tn')"
              :style="getCellStyle('tn')"
            >
              <span class="cell-value">{{ formatValue(matrix.trueNegative) }}</span>
              <span class="cell-label">TN</span>
            </div>
            <div class="matrix-cell total-cell">
              {{ matrix.falseNegative + matrix.trueNegative }}
            </div>
          </div>

          <!-- Totals Row -->
          <div class="matrix-row totals-row">
            <div class="matrix-cell row-header">
              {{ $t('scenarioManager.results.confusionMatrix.total') }}
            </div>
            <div class="matrix-cell total-cell">
              {{ matrix.truePositive + matrix.falseNegative }}
            </div>
            <div class="matrix-cell total-cell">
              {{ matrix.falsePositive + matrix.trueNegative }}
            </div>
            <div class="matrix-cell total-cell grand-total">
              {{ totalCount }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Metrics Summary -->
    <div class="metrics-summary" v-if="showMetrics">
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
          <LIcon size="14" class="info-icon">mdi-information-outline</LIcon>
        </LTooltip>
      </div>
      <div class="metric-item">
        <span class="metric-label">{{ $t('scenarioManager.results.confusionMatrix.recall') }}</span>
        <span class="metric-value" :class="getMetricClass(metrics.recall)">
          {{ metrics.recall !== null ? metrics.recall.toFixed(1) + '%' : '-' }}
        </span>
        <LTooltip :text="$t('scenarioManager.results.confusionMatrix.recallTooltip')">
          <LIcon size="14" class="info-icon">mdi-information-outline</LIcon>
        </LTooltip>
      </div>
      <div class="metric-item">
        <span class="metric-label">{{ $t('scenarioManager.results.confusionMatrix.f1Score') }}</span>
        <span class="metric-value" :class="getMetricClass(metrics.f1)">
          {{ metrics.f1 !== null ? metrics.f1.toFixed(2) : '-' }}
        </span>
        <LTooltip :text="$t('scenarioManager.results.confusionMatrix.f1Tooltip')">
          <LIcon size="14" class="info-icon">mdi-information-outline</LIcon>
        </LTooltip>
      </div>
    </div>

    <!-- Legend -->
    <div class="matrix-legend" v-if="showLegend">
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
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  /**
   * Confusion matrix data
   * { truePositive, falsePositive, trueNegative, falseNegative }
   */
  matrix: {
    type: Object,
    required: true,
    default: () => ({
      truePositive: 0,
      falsePositive: 0,
      trueNegative: 0,
      falseNegative: 0
    })
  },
  /**
   * Custom title
   */
  title: {
    type: String,
    default: ''
  },
  /**
   * Custom labels for the matrix
   */
  labels: {
    type: Object,
    default: () => ({})
  },
  /**
   * Show toggle between counts and percentages
   */
  showControls: {
    type: Boolean,
    default: true
  },
  /**
   * Show metrics summary (accuracy, precision, recall, F1)
   */
  showMetrics: {
    type: Boolean,
    default: true
  },
  /**
   * Show legend explaining TP, FP, TN, FN
   */
  showLegend: {
    type: Boolean,
    default: true
  },
  /**
   * Use heatmap coloring based on values
   */
  useHeatmap: {
    type: Boolean,
    default: true
  }
})

const { t } = useI18n()

// State
const displayMode = ref('counts')

// Computed
const totalCount = computed(() => {
  const { truePositive, falsePositive, trueNegative, falseNegative } = props.matrix
  return truePositive + falsePositive + trueNegative + falseNegative
})

const metrics = computed(() => {
  const { truePositive, falsePositive, trueNegative, falseNegative } = props.matrix
  const total = totalCount.value

  if (total === 0) {
    return { accuracy: null, precision: null, recall: null, f1: null }
  }

  // Accuracy = (TP + TN) / Total
  const accuracy = ((truePositive + trueNegative) / total) * 100

  // Precision = TP / (TP + FP) - How many predicted fakes are actually fake
  const precision = (truePositive + falsePositive) > 0
    ? (truePositive / (truePositive + falsePositive)) * 100
    : null

  // Recall = TP / (TP + FN) - How many actual fakes were detected
  const recall = (truePositive + falseNegative) > 0
    ? (truePositive / (truePositive + falseNegative)) * 100
    : null

  // F1 Score = 2 * (Precision * Recall) / (Precision + Recall)
  const f1 = (precision !== null && recall !== null && (precision + recall) > 0)
    ? (2 * (precision / 100) * (recall / 100)) / ((precision / 100) + (recall / 100))
    : null

  return { accuracy, precision, recall, f1 }
})

// Methods
function formatValue(value) {
  if (displayMode.value === 'percentages') {
    const total = totalCount.value
    if (total === 0) return '0%'
    return ((value / total) * 100).toFixed(1) + '%'
  }
  return value
}

function getCellClass(type) {
  const classes = [type]
  if (props.useHeatmap) {
    classes.push('heatmap')
  }
  return classes
}

function getCellStyle(type) {
  if (!props.useHeatmap) return {}

  const total = totalCount.value
  if (total === 0) return {}

  const value = {
    tp: props.matrix.truePositive,
    fp: props.matrix.falsePositive,
    tn: props.matrix.trueNegative,
    fn: props.matrix.falseNegative
  }[type]

  const intensity = Math.min(value / total, 1)

  // Correct predictions (TP, TN) - green tint
  // Incorrect predictions (FP, FN) - red tint
  if (type === 'tp' || type === 'tn') {
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
</script>

<style scoped>
.confusion-matrix-container {
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
  padding: 20px;
}

.matrix-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
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

.matrix-wrapper {
  display: flex;
  align-items: stretch;
  justify-content: center;
  margin-bottom: 20px;
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
  padding-right: 12px;
}

.axis-label.x-axis {
  padding-bottom: 8px;
  margin-left: 100px;
}

.matrix-content {
  display: flex;
  flex-direction: column;
}

.matrix-table {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.matrix-row {
  display: flex;
  gap: 2px;
}

.matrix-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 100px;
  min-height: 60px;
  padding: 8px 12px;
  font-size: 0.85rem;
}

.corner-cell {
  background: transparent;
}

.header-cell {
  background-color: rgba(var(--v-theme-on-surface), 0.04);
  font-weight: 600;
  border-radius: 6px 6px 0 0;
}

.header-cell.actual-fake {
  color: #e8a087;
}

.header-cell.actual-real {
  color: #98d4bb;
}

.row-header {
  background-color: rgba(var(--v-theme-on-surface), 0.04);
  font-weight: 600;
  min-width: 100px;
  justify-content: flex-start;
  border-radius: 6px 0 0 6px;
}

.row-header.predicted-fake {
  color: #e8a087;
}

.row-header.predicted-real {
  color: #98d4bb;
}

.value-cell {
  flex-direction: column;
  gap: 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.cell-value {
  font-size: 1.25rem;
  font-weight: 700;
}

.cell-label {
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  opacity: 0.6;
}

.value-cell.tp .cell-value,
.value-cell.tn .cell-value {
  color: #2e7d32;
}

.value-cell.fp .cell-value,
.value-cell.fn .cell-value {
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
  font-size: 0.75rem;
  text-transform: uppercase;
}

/* Metrics Summary */
.metrics-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 16px;
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  margin-bottom: 16px;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background-color: rgb(var(--v-theme-surface));
  border-radius: 6px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.metric-label {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.metric-value {
  font-size: 1rem;
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
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.legend-color {
  width: 16px;
  height: 16px;
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
  .matrix-cell {
    min-width: 70px;
    min-height: 50px;
    padding: 6px 8px;
    font-size: 0.75rem;
  }

  .cell-value {
    font-size: 1rem;
  }

  .row-header {
    min-width: 70px;
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

  .axis-label.x-axis {
    margin-left: 70px;
  }
}
</style>
