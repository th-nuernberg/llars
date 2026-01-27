<template>
  <div
    class="dimension-rating-card"
    :class="{
      'is-rated': modelValue !== null && modelValue !== undefined,
      'is-highlighted': highlighted
    }"
  >
    <!-- Dimension Header -->
    <div class="dimension-header">
      <div class="dimension-info">
        <span class="dimension-name">{{ dimensionName }}</span>
        <span v-if="weight" class="dimension-weight">
          {{ Math.round(weight * 100) }}%
        </span>
      </div>
      <v-tooltip v-if="description" location="top" max-width="300">
        <template #activator="{ props: tooltipProps }">
          <v-icon
            v-bind="tooltipProps"
            size="16"
            color="grey"
            class="help-icon"
          >
            mdi-help-circle-outline
          </v-icon>
        </template>
        {{ description }}
      </v-tooltip>
    </div>

    <!-- Rating Scale -->
    <div class="dimension-scale">
      <!-- Binary Scale (for dimensions with scale.type === 'binary') -->
      <BinaryLikertScale
        v-if="isBinaryScale"
        :model-value="modelValue"
        :disabled="disabled"
        :yes-label="binaryLabels.yes"
        :no-label="binaryLabels.no"
        @update:model-value="emitUpdate"
      />
      <!-- Standard Rating Scale -->
      <LRatingScale
        v-else
        :model-value="modelValue"
        :min="effectiveMin"
        :max="effectiveMax"
        :step="step"
        :labels="scaleLabels"
        :show-labels="showEndLabels"
        :show-value-labels="showValueLabels"
        :variant="variant"
        :size="size"
        :disabled="disabled"
        :aria-label="`${$t('evaluation.rating.rateDimension')}: ${dimensionName}`"
        @update:model-value="emitUpdate"
      />
    </div>

    <!-- Current Value Display (always reserve space) -->
    <div v-if="showCurrentValue && !isBinaryScale" class="current-value" :class="{ 'has-value': modelValue !== null }">
      <template v-if="modelValue !== null">
        <span class="value-badge" :class="getValueClass()">
          {{ modelValue }}/{{ effectiveMax }}
        </span>
        <span v-if="currentLabel" class="value-label">{{ currentLabel }}</span>
      </template>
      <span v-else class="value-placeholder">—</span>
    </div>
  </div>
</template>

<script setup>
/**
 * DimensionRatingCard - Rating card for a single dimension
 *
 * Displays a dimension name, description, and rating scale.
 * Used in the multi-dimensional rating interface.
 */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import LRatingScale from '@/components/common/LRatingScale.vue'
import BinaryLikertScale from '@/components/parts/BinaryLikertScale.vue'

const { locale } = useI18n()

const props = defineProps({
  modelValue: {
    type: Number,
    default: null
  },
  dimension: {
    type: Object,
    required: true
    // Expected: { id, name: {de, en}, description: {de, en}, weight }
  },
  labels: {
    type: Object,
    default: () => ({})
    // Expected: { 1: {de, en}, 2: {de, en}, ... }
  },
  min: {
    type: Number,
    default: 1
  },
  max: {
    type: Number,
    default: 5
  },
  step: {
    type: Number,
    default: 1
  },
  variant: {
    type: String,
    default: 'gradient'
  },
  size: {
    type: String,
    default: 'default'
  },
  disabled: {
    type: Boolean,
    default: false
  },
  highlighted: {
    type: Boolean,
    default: false
  },
  showEndLabels: {
    type: Boolean,
    default: true
  },
  showValueLabels: {
    type: Boolean,
    default: false
  },
  showCurrentValue: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue'])

// Get localized dimension name
const dimensionName = computed(() => {
  if (typeof props.dimension.name === 'string') {
    return props.dimension.name
  }
  return props.dimension.name?.[locale.value] || props.dimension.name?.de || props.dimension.id
})

// Get localized description
const description = computed(() => {
  if (!props.dimension.description) return null
  if (typeof props.dimension.description === 'string') {
    return props.dimension.description
  }
  return props.dimension.description?.[locale.value] || props.dimension.description?.de
})

// Get weight
const weight = computed(() => props.dimension.weight)

// Check if dimension has a binary scale
const isBinaryScale = computed(() => {
  return props.dimension.scale?.type === 'binary'
})

// Get effective min/max (from dimension scale or props)
const effectiveMin = computed(() => {
  return props.dimension.scale?.min ?? props.min
})

const effectiveMax = computed(() => {
  return props.dimension.scale?.max ?? props.max
})

// Get binary scale labels
const binaryLabels = computed(() => {
  const scale = props.dimension.scale
  if (!scale?.labels) return { yes: null, no: null }

  const yesLabel = scale.labels[1] || scale.labels['1']
  const noLabel = scale.labels[2] || scale.labels['2']

  return {
    yes: yesLabel ? (typeof yesLabel === 'string' ? yesLabel : (yesLabel[locale.value] || yesLabel.de)) : null,
    no: noLabel ? (typeof noLabel === 'string' ? noLabel : (noLabel[locale.value] || noLabel.de)) : null
  }
})

// Transform labels for LRatingScale
const scaleLabels = computed(() => {
  const result = {}

  // Set min/max labels from the provided labels
  if (props.labels) {
    const minLabel = props.labels[props.min]
    const maxLabel = props.labels[props.max]

    if (minLabel) {
      result.min = typeof minLabel === 'string' ? minLabel : (minLabel[locale.value] || minLabel.de)
    }
    if (maxLabel) {
      result.max = typeof maxLabel === 'string' ? maxLabel : (maxLabel[locale.value] || maxLabel.de)
    }

    // Individual value labels
    for (let v = props.min; v <= props.max; v += props.step) {
      const label = props.labels[v] || props.labels[String(v)]
      if (label) {
        result[v] = typeof label === 'string' ? label : (label[locale.value] || label.de)
      }
    }
  }

  return result
})

// Get current value's label
const currentLabel = computed(() => {
  if (props.modelValue === null) return null

  // Check dimension-specific scale labels first (for binary scales)
  if (props.dimension.scale?.labels) {
    const scaleLabel = props.dimension.scale.labels[props.modelValue] || props.dimension.scale.labels[String(props.modelValue)]
    if (scaleLabel) {
      return typeof scaleLabel === 'string' ? scaleLabel : (scaleLabel[locale.value] || scaleLabel.de)
    }
  }

  // Fallback to global labels
  const label = props.labels[props.modelValue] || props.labels[String(props.modelValue)]
  if (!label) return null
  return typeof label === 'string' ? label : (label[locale.value] || label.de)
})

// Get CSS class for value badge based on position
function getValueClass() {
  if (props.modelValue === null) return ''

  const min = effectiveMin.value
  const max = effectiveMax.value
  const range = max - min

  if (range === 0) return 'value-mid'

  const position = (props.modelValue - min) / range

  if (position <= 0.3) return 'value-low'
  if (position >= 0.7) return 'value-high'
  return 'value-mid'
}

function emitUpdate(value) {
  emit('update:modelValue', value)
}
</script>

<style scoped>
.dimension-rating-card {
  padding: 12px 14px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 10px 3px 10px 3px; /* Signature LLARS asymmetric style */
  background: rgba(var(--v-theme-surface-variant), 0.3);
  transition: all 0.2s ease;
}

.dimension-rating-card:hover {
  border-color: rgba(var(--v-theme-on-surface), 0.2);
  background: rgba(var(--v-theme-surface-variant), 0.5);
}

.dimension-rating-card.is-rated {
  border-color: var(--llars-primary, #b0ca97);
  background: rgba(176, 202, 151, 0.08);
}

.dimension-rating-card.is-highlighted {
  border-color: var(--llars-accent, #88c4c8);
  box-shadow: 0 0 0 2px rgba(136, 196, 200, 0.2);
}

/* Header */
.dimension-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.dimension-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dimension-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.dimension-weight {
  font-size: 0.7rem;
  font-weight: 500;
  padding: 2px 5px;
  border-radius: 4px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.help-icon {
  cursor: help;
  opacity: 0.6;
  transition: opacity 0.2s ease;
}

.help-icon:hover {
  opacity: 1;
}

/* Scale */
.dimension-scale {
  display: flex;
  justify-content: center;
}

/* Current Value Display - always reserve space */
.current-value {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  min-height: 28px; /* Reserve space for badge + label */
}

.value-placeholder {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.3);
}

.value-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  padding: 3px 8px;
  border-radius: 6px 2px 6px 2px;
  font-size: 0.8rem;
  font-weight: 600;
  color: white;
  background: var(--llars-secondary, #D1BC8A);
}

.value-badge.value-low {
  background: var(--llars-success, #98d4bb);
}

.value-badge.value-mid {
  background: var(--llars-secondary, #D1BC8A);
}

.value-badge.value-high {
  background: var(--llars-danger, #e8a087);
}

.value-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-style: italic;
}

/* Responsive */
@media (max-width: 600px) {
  .dimension-rating-card {
    padding: 10px 12px;
  }

  .dimension-name {
    font-size: 0.8rem;
  }

  .current-value {
    flex-direction: column;
    gap: 4px;
    min-height: 40px;
  }
}
</style>
