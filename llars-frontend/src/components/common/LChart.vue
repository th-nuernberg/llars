<template>
  <div class="l-chart" :class="{ 'l-chart--loading': loading }">
    <div v-if="title || $slots.title" class="l-chart__header">
      <slot name="title">
        <span class="l-chart__title">{{ title }}</span>
      </slot>
      <slot name="actions" />
    </div>
    <div class="l-chart__container" :style="containerStyle">
      <canvas ref="canvasRef" />
      <div v-if="loading" class="l-chart__loading">
        <v-progress-circular indeterminate size="24" color="primary" />
      </div>
      <div v-else-if="!hasData" class="l-chart__empty">
        <LIcon icon="mdi-chart-line" size="32" color="grey-lighten-1" />
        <span>{{ emptyText }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * LChart - LLARS Global Chart Component
 *
 * A lightweight, performant line chart component for real-time metrics.
 * Uses Canvas 2D for optimal performance with frequent updates.
 *
 * Features:
 *   - Smooth line rendering with anti-aliasing
 *   - Gradient fill under the line
 *   - Responsive sizing
 *   - Multiple data series support
 *   - LLARS color palette integration
 *
 * Usage:
 *   <LChart
 *     :data="[10, 20, 15, 30, 25]"
 *     :max-points="60"
 *     color="primary"
 *     title="CPU Usage"
 *   />
 *
 *   <!-- Multiple series -->
 *   <LChart
 *     :series="[
 *       { data: rxData, color: 'success', label: 'RX' },
 *       { data: txData, color: 'accent', label: 'TX' }
 *     ]"
 *   />
 */
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'

const props = defineProps({
  /** Single data series (array of numbers) */
  data: {
    type: Array,
    default: () => []
  },
  /** Multiple data series */
  series: {
    type: Array,
    default: () => []
  },
  /** Maximum number of data points to display */
  maxPoints: {
    type: Number,
    default: 60
  },
  /** Chart height in pixels */
  height: {
    type: [Number, String],
    default: 100
  },
  /** Line color (LLARS color name or hex) */
  color: {
    type: String,
    default: 'primary'
  },
  /** Whether to show gradient fill */
  fill: {
    type: Boolean,
    default: true
  },
  /** Whether to show grid lines */
  grid: {
    type: Boolean,
    default: true
  },
  /** Chart title */
  title: {
    type: String,
    default: ''
  },
  /** Loading state */
  loading: {
    type: Boolean,
    default: false
  },
  /** Empty state text */
  emptyText: {
    type: String,
    default: 'Keine Daten'
  },
  /** Min Y value (auto if not set) */
  minY: {
    type: Number,
    default: null
  },
  /** Max Y value (auto if not set) */
  maxY: {
    type: Number,
    default: null
  },
  /** Line width */
  lineWidth: {
    type: Number,
    default: 2
  },
  /** Enable smooth curves */
  smooth: {
    type: Boolean,
    default: true
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
  danger: '#e8a087',
  gray: '#9e9e9e'
}

const canvasRef = ref(null)
let ctx = null
let animationId = null
let resizeObserver = null

const containerStyle = computed(() => ({
  height: typeof props.height === 'number' ? `${props.height}px` : props.height
}))

const hasData = computed(() => {
  if (props.series.length > 0) {
    return props.series.some(s => s.data && s.data.length > 0)
  }
  return props.data && props.data.length > 0
})

const normalizedSeries = computed(() => {
  if (props.series.length > 0) {
    return props.series.map(s => ({
      data: s.data || [],
      color: getColor(s.color || 'primary'),
      label: s.label || ''
    }))
  }
  return [{
    data: props.data,
    color: getColor(props.color),
    label: ''
  }]
})

function getColor(colorName) {
  return colors[colorName] || colorName
}

function hexToRgba(hex, alpha) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  if (!result) return `rgba(0, 0, 0, ${alpha})`
  const r = parseInt(result[1], 16)
  const g = parseInt(result[2], 16)
  const b = parseInt(result[3], 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

function draw() {
  if (!ctx || !canvasRef.value) return

  const canvas = canvasRef.value
  const dpr = window.devicePixelRatio || 1
  const rect = canvas.getBoundingClientRect()

  // Set canvas size with device pixel ratio for sharp rendering
  if (canvas.width !== rect.width * dpr || canvas.height !== rect.height * dpr) {
    canvas.width = rect.width * dpr
    canvas.height = rect.height * dpr
    ctx.scale(dpr, dpr)
  }

  const width = rect.width
  const height = rect.height

  // Clear canvas
  ctx.clearRect(0, 0, width, height)

  if (!hasData.value) return

  // Calculate Y range
  let allValues = []
  normalizedSeries.value.forEach(s => {
    allValues = allValues.concat(s.data)
  })

  let minY = props.minY !== null ? props.minY : Math.min(...allValues)
  let maxY = props.maxY !== null ? props.maxY : Math.max(...allValues)

  // Add padding
  const range = maxY - minY || 1
  if (props.minY === null) minY = Math.max(0, minY - range * 0.1)
  if (props.maxY === null) maxY = maxY + range * 0.1

  const padding = { top: 8, right: 8, bottom: 8, left: 8 }
  const chartWidth = width - padding.left - padding.right
  const chartHeight = height - padding.top - padding.bottom

  // Draw grid
  if (props.grid) {
    ctx.strokeStyle = 'rgba(128, 128, 128, 0.15)'
    ctx.lineWidth = 1

    // Horizontal grid lines
    for (let i = 0; i <= 4; i++) {
      const y = padding.top + (chartHeight / 4) * i
      ctx.beginPath()
      ctx.moveTo(padding.left, y)
      ctx.lineTo(width - padding.right, y)
      ctx.stroke()
    }
  }

  // Draw each series
  normalizedSeries.value.forEach(series => {
    if (!series.data || series.data.length === 0) return

    const data = series.data.slice(-props.maxPoints)
    const stepX = chartWidth / (props.maxPoints - 1)

    // Calculate points
    const points = data.map((value, index) => {
      const x = padding.left + index * stepX + (props.maxPoints - data.length) * stepX
      const y = padding.top + chartHeight - ((value - minY) / (maxY - minY)) * chartHeight
      return { x, y }
    })

    if (points.length < 2) return

    // Draw fill gradient
    if (props.fill) {
      ctx.beginPath()
      ctx.moveTo(points[0].x, height - padding.bottom)

      if (props.smooth && points.length > 2) {
        drawSmoothLine(ctx, points, true)
      } else {
        points.forEach(p => ctx.lineTo(p.x, p.y))
      }

      ctx.lineTo(points[points.length - 1].x, height - padding.bottom)
      ctx.closePath()

      const gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom)
      gradient.addColorStop(0, hexToRgba(series.color, 0.3))
      gradient.addColorStop(1, hexToRgba(series.color, 0.05))
      ctx.fillStyle = gradient
      ctx.fill()
    }

    // Draw line
    ctx.beginPath()
    ctx.moveTo(points[0].x, points[0].y)

    if (props.smooth && points.length > 2) {
      drawSmoothLine(ctx, points, false)
    } else {
      points.forEach(p => ctx.lineTo(p.x, p.y))
    }

    ctx.strokeStyle = series.color
    ctx.lineWidth = props.lineWidth
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    ctx.stroke()
  })
}

function drawSmoothLine(ctx, points, isFirst) {
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i - 1] || points[i]
    const p1 = points[i]
    const p2 = points[i + 1]
    const p3 = points[i + 2] || p2

    const cp1x = p1.x + (p2.x - p0.x) / 6
    const cp1y = p1.y + (p2.y - p0.y) / 6
    const cp2x = p2.x - (p3.x - p1.x) / 6
    const cp2y = p2.y - (p3.y - p1.y) / 6

    if (i === 0 && isFirst) {
      ctx.lineTo(p1.x, p1.y)
    }
    ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p2.x, p2.y)
  }
}

function handleResize() {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  animationId = requestAnimationFrame(() => {
    draw()
  })
}

onMounted(() => {
  nextTick(() => {
    if (canvasRef.value) {
      ctx = canvasRef.value.getContext('2d')
      draw()

      resizeObserver = new ResizeObserver(handleResize)
      resizeObserver.observe(canvasRef.value.parentElement)
    }
  })
})

onBeforeUnmount(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
})

// Redraw when data changes
watch(
  () => [props.data, props.series],
  () => {
    if (animationId) {
      cancelAnimationFrame(animationId)
    }
    animationId = requestAnimationFrame(() => {
      draw()
    })
  },
  { deep: true }
)
</script>

<style scoped>
.l-chart {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.l-chart__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.l-chart__title {
  font-size: 0.75rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.l-chart__container {
  position: relative;
  width: 100%;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px 2px 8px 2px;
  overflow: hidden;
}

.l-chart__container canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.l-chart__loading,
.l-chart__empty {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: rgba(var(--v-theme-surface), 0.8);
}

.l-chart__empty {
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 0.75rem;
}

.l-chart--loading .l-chart__container canvas {
  opacity: 0.3;
}
</style>
