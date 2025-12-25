<template>
  <div class="l-gauge" :class="gaugeClasses">
    <div class="l-gauge__header">
      <div class="l-gauge__icon-wrapper" :style="iconStyle">
        <v-icon :icon="icon" :size="iconSize" />
      </div>
      <div class="l-gauge__info">
        <span class="l-gauge__label">{{ label }}</span>
        <span class="l-gauge__value">
          <slot name="value">{{ formattedValue }}</slot>
        </span>
      </div>
    </div>

    <div v-if="showProgress" class="l-gauge__progress">
      <div class="l-gauge__track">
        <div
          class="l-gauge__fill"
          :style="fillStyle"
        />
      </div>
      <span v-if="showPercent" class="l-gauge__percent">{{ Math.round(percent) }}%</span>
    </div>

    <div v-if="subtitle || $slots.subtitle" class="l-gauge__subtitle">
      <slot name="subtitle">{{ subtitle }}</slot>
    </div>
  </div>
</template>

<script setup>
/**
 * LGauge - LLARS Global Gauge/Metric Component
 *
 * A compact metric display with optional progress bar.
 * Perfect for CPU, RAM, disk usage, and other percentage-based metrics.
 *
 * Features:
 *   - Colored icon with background
 *   - Animated progress bar
 *   - Automatic color transitions based on value
 *   - Support for custom value formatting
 *
 * Usage:
 *   <LGauge
 *     icon="mdi-cpu-64-bit"
 *     label="CPU"
 *     :value="54.2"
 *     suffix="%"
 *     :percent="54.2"
 *   />
 *
 *   <LGauge
 *     icon="mdi-memory"
 *     label="RAM"
 *     :value="16.4"
 *     suffix="GB"
 *     :percent="72"
 *     subtitle="16.4 / 22.8 GB"
 *     color-mode="threshold"
 *   />
 */
import { computed } from 'vue'

const props = defineProps({
  /** MDI icon name */
  icon: {
    type: String,
    default: 'mdi-chart-box'
  },
  /** Icon size */
  iconSize: {
    type: [Number, String],
    default: 20
  },
  /** Metric label */
  label: {
    type: String,
    required: true
  },
  /** Metric value */
  value: {
    type: [Number, String],
    default: 0
  },
  /** Value suffix (e.g., '%', 'GB', 'ms') */
  suffix: {
    type: String,
    default: ''
  },
  /** Percentage for progress bar (0-100) */
  percent: {
    type: Number,
    default: null
  },
  /** Show progress bar */
  showProgress: {
    type: Boolean,
    default: true
  },
  /** Show percentage text */
  showPercent: {
    type: Boolean,
    default: false
  },
  /** Subtitle text */
  subtitle: {
    type: String,
    default: ''
  },
  /** Base color (LLARS color name or hex) */
  color: {
    type: String,
    default: 'primary'
  },
  /**
   * Color mode:
   * - 'fixed': Use the specified color
   * - 'threshold': Green < 60%, Yellow 60-80%, Red > 80%
   * - 'inverse': Red < 20%, Yellow 20-40%, Green > 40%
   */
  colorMode: {
    type: String,
    default: 'threshold',
    validator: (v) => ['fixed', 'threshold', 'inverse'].includes(v)
  },
  /** Compact mode */
  compact: {
    type: Boolean,
    default: false
  },
  /** Loading state */
  loading: {
    type: Boolean,
    default: false
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

const gaugeClasses = computed(() => ({
  'l-gauge--compact': props.compact,
  'l-gauge--loading': props.loading
}))

const formattedValue = computed(() => {
  if (typeof props.value === 'number') {
    // Format numbers nicely
    if (props.value >= 1000000) {
      return (props.value / 1000000).toFixed(1) + 'M' + props.suffix
    }
    if (props.value >= 1000) {
      return (props.value / 1000).toFixed(1) + 'K' + props.suffix
    }
    if (Number.isInteger(props.value)) {
      return props.value + props.suffix
    }
    return props.value.toFixed(1) + props.suffix
  }
  return props.value + props.suffix
})

const effectiveColor = computed(() => {
  if (props.colorMode === 'fixed') {
    return getColor(props.color)
  }

  const pct = props.percent ?? 0

  if (props.colorMode === 'threshold') {
    if (pct < 60) return colors.success
    if (pct < 80) return colors.warning
    return colors.danger
  }

  if (props.colorMode === 'inverse') {
    if (pct < 20) return colors.danger
    if (pct < 40) return colors.warning
    return colors.success
  }

  return getColor(props.color)
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

const iconStyle = computed(() => ({
  backgroundColor: hexToRgba(effectiveColor.value, 0.15),
  color: effectiveColor.value
}))

const fillStyle = computed(() => ({
  width: `${Math.min(100, Math.max(0, props.percent ?? 0))}%`,
  backgroundColor: effectiveColor.value
}))
</script>

<style scoped>
.l-gauge {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: rgb(var(--v-theme-surface));
  border-radius: 12px 4px 12px 4px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  transition: all 0.2s ease;
}

.l-gauge:hover {
  border-color: rgba(var(--v-theme-on-surface), 0.12);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.l-gauge--compact {
  padding: 8px;
  gap: 6px;
}

.l-gauge--compact .l-gauge__icon-wrapper {
  width: 32px;
  height: 32px;
}

.l-gauge--compact .l-gauge__label {
  font-size: 0.7rem;
}

.l-gauge--compact .l-gauge__value {
  font-size: 1rem;
}

.l-gauge__header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.l-gauge__icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px 2px 8px 2px;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.l-gauge__info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.l-gauge__label {
  font-size: 0.75rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.l-gauge__value {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.2;
}

.l-gauge__progress {
  display: flex;
  align-items: center;
  gap: 8px;
}

.l-gauge__track {
  flex: 1;
  height: 6px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 3px;
  overflow: hidden;
}

.l-gauge__fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease, background-color 0.3s ease;
}

.l-gauge__percent {
  font-size: 0.75rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.6);
  min-width: 32px;
  text-align: right;
}

.l-gauge__subtitle {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: -2px;
}

.l-gauge--loading {
  opacity: 0.6;
  pointer-events: none;
}

.l-gauge--loading .l-gauge__fill {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
