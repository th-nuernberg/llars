<template>
  <div class="dimension-radar-chart">
    <div v-if="title" class="chart-title">{{ title }}</div>
    <svg
      ref="svgRef"
      :viewBox="`0 0 ${size} ${size}`"
      class="radar-svg"
    >
      <!-- Background circles -->
      <g class="radar-grid">
        <circle
          v-for="level in gridLevels"
          :key="'grid-' + level"
          :cx="center"
          :cy="center"
          :r="(radius / gridLevels) * level"
          fill="none"
          stroke="rgba(128, 128, 128, 0.2)"
          stroke-width="1"
        />
      </g>

      <!-- Axis lines -->
      <g class="radar-axes">
        <line
          v-for="(dim, i) in dimensions"
          :key="'axis-' + i"
          :x1="center"
          :y1="center"
          :x2="getPointX(i, 1)"
          :y2="getPointY(i, 1)"
          stroke="rgba(128, 128, 128, 0.3)"
          stroke-width="1"
        />
      </g>

      <!-- Data polygons -->
      <g class="radar-data">
        <polygon
          v-for="(series, seriesIndex) in normalizedSeries"
          :key="'polygon-' + seriesIndex"
          :points="getPolygonPoints(series)"
          :fill="hexToRgba(series.color, 0.2)"
          :stroke="series.color"
          stroke-width="2"
          class="data-polygon"
        />
        <!-- Data points -->
        <template v-for="(series, seriesIndex) in normalizedSeries" :key="'points-' + seriesIndex">
          <circle
            v-for="(value, i) in series.values"
            :key="'point-' + seriesIndex + '-' + i"
            :cx="getPointX(i, value / maxValue)"
            :cy="getPointY(i, value / maxValue)"
            :r="4"
            :fill="series.color"
            class="data-point"
          />
        </template>
      </g>

      <!-- Axis labels -->
      <g class="radar-labels">
        <text
          v-for="(dim, i) in dimensions"
          :key="'label-' + i"
          :x="getLabelX(i)"
          :y="getLabelY(i)"
          :text-anchor="getLabelAnchor(i)"
          :dominant-baseline="getLabelBaseline(i)"
          class="axis-label"
        >
          {{ dim.label }}
        </text>
      </g>
    </svg>

    <!-- Legend -->
    <div v-if="showLegend && normalizedSeries.length > 1" class="chart-legend">
      <div
        v-for="(series, i) in normalizedSeries"
        :key="'legend-' + i"
        class="legend-item"
      >
        <span class="legend-color" :style="{ backgroundColor: series.color }"></span>
        <span class="legend-label">{{ series.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * DimensionRadarChart - Radar/Spider chart for multi-dimensional ratings
 *
 * Displays average scores across multiple dimensions in a radar chart format.
 * Supports multiple series (e.g., Human vs LLM averages).
 *
 * Usage:
 *   <DimensionRadarChart
 *     :dimensions="[
 *       { id: 'coherence', label: i18n.global.t('auto.44b10d4ad944b1cc') },
 *       { id: 'fluency', label: i18n.global.t('auto.a5246285acd6ab26') },
 *       { id: 'relevance', label: i18n.global.t('auto.fe2f62574eda312d') }
 *     ]"
 *     :series="[
 *       { label: i18n.global.t('auto.a0c1690cc2296c36'), values: [4.2, 3.8, 4.5], color: 'primary' },
 *       { label: i18n.global.t('auto.5f693646b7b498d3'), values: [4.0, 4.1, 4.3], color: 'accent' }
 *     ]"
 *     :max-value="5"
 *   />
 */
import { ref, computed } from 'vue'
import { i18n } from '@/i18n'

const props = defineProps({
  /** Dimension definitions with id and label */
  dimensions: {
    type: Array,
    required: true
  },
  /** Data series - each with label, values array, and optional color */
  series: {
    type: Array,
    default: () => []
  },
  /** Single series values (shorthand when only one series) */
  values: {
    type: Array,
    default: () => []
  },
  /** Maximum value on the scale */
  maxValue: {
    type: Number,
    default: 5
  },
  /** Chart title */
  title: {
    type: String,
    default: ''
  },
  /** Show legend */
  showLegend: {
    type: Boolean,
    default: true
  },
  /** SVG size */
  size: {
    type: Number,
    default: 300
  }
})

// LLARS color palette
const colors = {
  primary: '#b0ca97',
  secondary: '#D1BC8A',
  accent: '#88c4c8',
  success: '#98d4bb',
  info: '#a8c5e2',
  warning: '#e8c87a',
  danger: '#e8a087'
}

const svgRef = ref(null)
const gridLevels = 5
const center = computed(() => props.size / 2)
const radius = computed(() => (props.size / 2) - 40) // Leave space for labels
const maxValue = computed(() => props.maxValue)

const normalizedSeries = computed(() => {
  if (props.series.length > 0) {
    return props.series.map((s, i) => ({
      label: s.label || `Series ${i + 1}`,
      values: s.values || [],
      color: getColor(s.color || (i === 0 ? 'primary' : 'accent'))
    }))
  }
  if (props.values.length > 0) {
    return [{
      label: i18n.global.t('auto.5dd135d1bcfa7f63'),
      values: props.values,
      color: getColor('primary')
    }]
  }
  return []
})

function getColor(colorName) {
  return colors[colorName] || colorName
}

function hexToRgba(hex, alpha) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  if (!result) return `rgba(176, 202, 151, ${alpha})`
  const r = parseInt(result[1], 16)
  const g = parseInt(result[2], 16)
  const b = parseInt(result[3], 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

function getAngle(index) {
  const angleOffset = -Math.PI / 2 // Start from top
  return angleOffset + (2 * Math.PI * index) / props.dimensions.length
}

function getPointX(index, ratio) {
  const angle = getAngle(index)
  return center.value + radius.value * ratio * Math.cos(angle)
}

function getPointY(index, ratio) {
  const angle = getAngle(index)
  return center.value + radius.value * ratio * Math.sin(angle)
}

function getPolygonPoints(series) {
  return series.values
    .map((value, i) => {
      const ratio = value / maxValue.value
      return `${getPointX(i, ratio)},${getPointY(i, ratio)}`
    })
    .join(' ')
}

function getLabelX(index) {
  const angle = getAngle(index)
  const labelRadius = radius.value + 20
  return center.value + labelRadius * Math.cos(angle)
}

function getLabelY(index) {
  const angle = getAngle(index)
  const labelRadius = radius.value + 20
  return center.value + labelRadius * Math.sin(angle)
}

function getLabelAnchor(index) {
  const angle = getAngle(index)
  const x = Math.cos(angle)
  if (Math.abs(x) < 0.1) return 'middle'
  return x > 0 ? 'start' : 'end'
}

function getLabelBaseline(index) {
  const angle = getAngle(index)
  const y = Math.sin(angle)
  if (Math.abs(y) < 0.1) return 'middle'
  return y > 0 ? 'hanging' : 'auto'
}
</script>

<style scoped>
.dimension-radar-chart {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  background-color: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 12px;
}

.chart-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin-bottom: 8px;
}

.radar-svg {
  width: 100%;
  max-width: 300px;
  height: auto;
}

.axis-label {
  font-size: 10px;
  font-weight: 500;
  fill: rgba(var(--v-theme-on-surface), 0.7);
}

.data-polygon {
  transition: opacity 0.2s;
}

.data-polygon:hover {
  opacity: 0.8;
}

.data-point {
  transition: r 0.2s;
}

.data-point:hover {
  r: 6;
}

.chart-legend {
  display: flex;
  gap: 16px;
  margin-top: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.legend-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}
</style>
