<template>
  <div class="metric-item" :style="{ '--metric-color': color }">
    <div class="metric-header">
      <div class="metric-name">
        <LIcon :size="18" :color="color" class="mr-2">{{ icon }}</LIcon>
        <span>{{ name }}</span>
      </div>
      <LTooltip max-width="300">
        <template #default>
          <LBtn variant="text" size="x-small" icon>
            <LIcon size="16">mdi-information-outline</LIcon>
          </LBtn>
        </template>
        <template #text>
          <div class="tooltip-content">
            <p class="tooltip-description">{{ description }}</p>
            <p class="tooltip-range">
              <strong>{{ $t('evaluationAssistant.metrics.rangeLabel') }}:</strong> {{ range }}
            </p>
          </div>
        </template>
      </LTooltip>
    </div>

    <div class="metric-body">
      <div class="metric-value" :class="valueClass">
        {{ formattedValue }}
      </div>
      <div v-if="interpretation" class="metric-interpretation">
        {{ interpretation }}
      </div>
    </div>

    <!-- Visual indicator bar -->
    <div class="metric-bar">
      <div class="metric-bar-fill" :style="{ width: barWidth }"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: {
    type: String,
    required: true
  },
  value: {
    type: Number,
    required: true
  },
  interpretation: {
    type: String,
    default: ''
  },
  description: {
    type: String,
    default: ''
  },
  range: {
    type: String,
    default: ''
  },
  icon: {
    type: String,
    default: 'mdi-chart-line'
  },
  color: {
    type: String,
    default: '#b0ca97'
  },
  isPercent: {
    type: Boolean,
    default: false
  }
})

const formattedValue = computed(() => {
  if (props.value === null || props.value === undefined) return 'N/A'
  if (props.isPercent) return `${props.value.toFixed(1)}%`
  return props.value.toFixed(3)
})

const valueClass = computed(() => {
  if (props.value === null || props.value === undefined) return ''

  // For Kappa/Alpha values (-1 to 1 or 0 to 1)
  if (!props.isPercent) {
    if (props.value >= 0.8) return 'value-excellent'
    if (props.value >= 0.6) return 'value-good'
    if (props.value >= 0.4) return 'value-moderate'
    if (props.value >= 0.2) return 'value-fair'
    return 'value-poor'
  }

  // For percentage values
  if (props.value >= 90) return 'value-excellent'
  if (props.value >= 75) return 'value-good'
  if (props.value >= 60) return 'value-moderate'
  if (props.value >= 40) return 'value-fair'
  return 'value-poor'
})

const barWidth = computed(() => {
  if (props.value === null || props.value === undefined) return '0%'

  if (props.isPercent) {
    return `${Math.max(0, Math.min(100, props.value))}%`
  }

  // Map -1 to 1 range to 0-100%
  const normalizedValue = ((props.value + 1) / 2) * 100
  return `${Math.max(0, Math.min(100, normalizedValue))}%`
})
</script>

<style scoped>
.metric-item {
  padding: 12px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  border-left: 3px solid var(--metric-color);
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.metric-name {
  display: flex;
  align-items: center;
  font-weight: 500;
  font-size: 0.875rem;
}

.metric-body {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 1.5rem;
  font-weight: 700;
  font-family: 'Roboto Mono', monospace;
}

.value-excellent { color: #4CAF50; }
.value-good { color: #8BC34A; }
.value-moderate { color: #FFC107; }
.value-fair { color: #FF9800; }
.value-poor { color: #F44336; }

.metric-interpretation {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  text-align: right;
  max-width: 50%;
}

.metric-bar {
  height: 4px;
  background: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.metric-bar-fill {
  height: 100%;
  background: var(--metric-color);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.tooltip-content {
  padding: 4px;
}

.tooltip-description {
  margin-bottom: 8px;
}

.tooltip-range {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.8);
}
</style>
