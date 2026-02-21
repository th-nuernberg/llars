<template>
  <div class="l-rating-distribution" :class="[`size-${size}`]">
    <!-- Header -->
    <div class="distribution-header" v-if="showHeader">
      <span class="distribution-label">{{ label }}</span>
      <span class="distribution-scale" v-if="scaleMin !== null && scaleMax !== null">
        {{ $t('scenarioManager.results.scale') }}: {{ scaleMin }} - {{ scaleMax }}
      </span>
    </div>

    <!-- Distribution Grid -->
    <div class="distribution-grid" v-if="normalizedItems.length > 0">
      <div
        v-for="(item, index) in normalizedItems"
        :key="item.value"
        class="distribution-cell"
        :class="{ 'clickable': clickable }"
        :style="{ backgroundColor: getCellColor(item.percentage) }"
        @click="clickable && $emit('cell-click', item)"
      >
        <span class="cell-value">{{ item.value }}</span>
        <span class="cell-count">{{ item.count }}</span>
        <span class="cell-percent">{{ formatPercentage(item.percentage) }}</span>
      </div>
    </div>

    <!-- Empty State -->
    <div class="distribution-grid empty-grid" v-else-if="scaleMin !== null && scaleMax !== null">
      <div
        v-for="value in getScaleValues()"
        :key="value"
        class="distribution-cell empty-cell"
      >
        <span class="cell-value">{{ value }}</span>
        <span class="cell-count">0</span>
        <span class="cell-percent">-</span>
      </div>
    </div>

    <!-- No Scale State -->
    <div v-else class="no-data-panel">
      <p class="text-medium-emphasis">{{ emptyText || $t('scenarioManager.evaluation.noRatingsYet') }}</p>
    </div>

    <!-- Hint for empty state -->
    <p v-if="normalizedItems.length === 0 && scaleMin !== null" class="no-data-hint">
      {{ emptyText || $t('scenarioManager.evaluation.noRatingsYet') }}
    </p>
  </div>
</template>

<script setup>
/**
 * LRatingDistribution - Global rating distribution heatmap component
 *
 * Shows distribution of ratings across a scale (e.g., 1-5 Likert scale).
 * Each cell shows the value, count, and percentage with color intensity.
 *
 * Usage:
 *   <LRatingDistribution
 *     :items="[{ value: 1, count: 5, percentage: 10 }, { value: 2, count: 15, percentage: 30 }, ...]"
 *     :scale-min="1"
 *     :scale-max="5"
 *     label="Kohärenz"
 *     size="compact"
 *   />
 */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  /**
   * Distribution items
   * [{ value: number, count: number, percentage: number }]
   */
  items: {
    type: Array,
    default: () => []
  },
  /**
   * Dimension/rating label
   */
  label: {
    type: String,
    default: ''
  },
  /**
   * Scale minimum value
   */
  scaleMin: {
    type: Number,
    default: null
  },
  /**
   * Scale maximum value
   */
  scaleMax: {
    type: Number,
    default: null
  },
  /**
   * Scale step (for generating empty cells)
   */
  scaleStep: {
    type: Number,
    default: 1
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
   * Show header with label and scale info
   */
  showHeader: {
    type: Boolean,
    default: true
  },
  /**
   * Make cells clickable
   */
  clickable: {
    type: Boolean,
    default: false
  },
  /**
   * Primary color for high values (hex)
   */
  primaryColor: {
    type: String,
    default: '#b0ca97'
  },
  /**
   * Empty/low color (hex)
   */
  emptyColor: {
    type: String,
    default: '#f5f5f5'
  },
  /**
   * Text for empty state
   */
  emptyText: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['cell-click'])

const { t } = useI18n()

// Computed: Normalize items to ensure all scale values are present
const normalizedItems = computed(() => {
  if (!props.items || props.items.length === 0) return []
  return props.items
})

// Methods
function getScaleValues() {
  if (props.scaleMin === null || props.scaleMax === null) return []
  const values = []
  for (let v = props.scaleMin; v <= props.scaleMax; v += props.scaleStep) {
    values.push(v)
  }
  return values
}

function getCellColor(percentage) {
  if (percentage === 0 || percentage === null || percentage === undefined) {
    return props.emptyColor
  }

  // Parse primary color
  const hex = props.primaryColor.replace('#', '')
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)

  // Gradient from light to primary color based on percentage
  const intensity = Math.min(percentage / 100, 1)
  const finalR = Math.round(255 - (255 - r) * intensity)
  const finalG = Math.round(255 - (255 - g) * intensity)
  const finalB = Math.round(255 - (255 - b) * intensity)

  return `rgb(${finalR}, ${finalG}, ${finalB})`
}

function formatPercentage(percentage) {
  if (percentage === null || percentage === undefined) return '-'
  return `${percentage}%`
}
</script>

<style scoped>
.l-rating-distribution {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Size variants */
.l-rating-distribution.size-compact .distribution-cell {
  min-width: 50px;
  min-height: 56px;
  padding: 6px;
}

.l-rating-distribution.size-compact .cell-value {
  font-size: 0.95rem;
}

.l-rating-distribution.size-compact .cell-count {
  font-size: 0.75rem;
}

.l-rating-distribution.size-compact .cell-percent {
  font-size: 0.6rem;
}

.l-rating-distribution.size-large .distribution-cell {
  min-width: 80px;
  min-height: 90px;
}

.l-rating-distribution.size-large .cell-value {
  font-size: 1.3rem;
}

/* Header */
.distribution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.distribution-label {
  font-weight: 600;
  font-size: 0.9rem;
}

.distribution-scale {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Distribution Grid */
.distribution-grid {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.distribution-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 64px;
  min-height: 72px;
  padding: 8px;
  border-radius: 8px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.distribution-cell.clickable {
  cursor: pointer;
}

.distribution-cell:hover {
  transform: scale(1.05);
}

.distribution-cell.clickable:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.cell-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.7);
}

.cell-count {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.6);
  margin-top: 2px;
}

.cell-percent {
  font-size: 0.7rem;
  color: rgba(0, 0, 0, 0.5);
}

/* Empty State */
.empty-grid .empty-cell {
  background-color: rgba(var(--v-theme-on-surface), 0.05);
  border: 1px dashed rgba(var(--v-theme-on-surface), 0.15);
}

.empty-grid .empty-cell .cell-value {
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.empty-grid .empty-cell .cell-count,
.empty-grid .empty-cell .cell-percent {
  color: rgba(var(--v-theme-on-surface), 0.3);
}

.no-data-panel {
  padding: 16px;
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-size: 0.85rem;
}

.no-data-hint {
  text-align: center;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: 8px;
}

/* Responsive */
@media (max-width: 600px) {
  .distribution-grid {
    justify-content: center;
  }

  .distribution-cell {
    min-width: 56px;
    min-height: 64px;
  }
}
</style>
