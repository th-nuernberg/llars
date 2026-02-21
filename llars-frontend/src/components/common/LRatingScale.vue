<template>
  <div class="l-rating-scale" :class="containerClasses">
    <!-- Optional Header -->
    <div v-if="showLabels && (labels.min || labels.max)" class="scale-header">
      <span class="scale-label scale-label--min">{{ labels.min }}</span>
      <span class="scale-label scale-label--max">{{ labels.max }}</span>
    </div>

    <!-- Scale Buttons -->
    <div class="scale-buttons" role="radiogroup" :aria-label="ariaLabel">
      <button
        v-for="value in scaleValues"
        :key="value"
        type="button"
        role="radio"
        class="scale-button"
        :class="getButtonClasses(value)"
        :aria-checked="modelValue === value"
        :aria-label="`${value} ${labels[value] || ''}`"
        :disabled="disabled"
        @click="selectValue(value)"
        @keydown.enter.prevent="selectValue(value)"
        @keydown.space.prevent="selectValue(value)"
      >
        <span class="scale-value">{{ value }}</span>
        <span v-if="labels[value] && showValueLabels" class="scale-value-label">
          {{ labels[value] }}
        </span>
      </button>
    </div>

    <!-- Optional Bottom Labels (individual) -->
    <div v-if="showValueLabels && hasIndividualLabels" class="scale-labels-row">
      <span
        v-for="value in scaleValues"
        :key="'label-' + value"
        class="scale-individual-label"
        :class="{ 'is-selected': modelValue === value }"
      >
        {{ labels[value] || '' }}
      </span>
    </div>
  </div>
</template>

<script setup>
/**
 * LRatingScale - LLARS Likert Scale Component
 *
 * A reusable rating scale component with the signature LLARS styling.
 * Supports 5-point and 7-point Likert scales with customizable labels.
 *
 * Features:
 *   - Asymmetric border-radius matching LLARS design
 *   - Color-coded values (green for positive, red for negative)
 *   - Size progression (smaller at extremes, larger in middle)
 *   - Keyboard accessible
 *   - Dark/light mode support
 *
 * Usage:
 *   <LRatingScale v-model="rating" :min="1" :max="5" />
 *   <LRatingScale v-model="rating" :labels="{ min: 'Poor', max: 'Excellent' }" />
 */
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Number,
    default: null
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
  labels: {
    type: Object,
    default: () => ({})
  },
  showLabels: {
    type: Boolean,
    default: true
  },
  showValueLabels: {
    type: Boolean,
    default: false
  },
  size: {
    type: String,
    default: 'default',
    validator: (v) => ['small', 'default', 'large'].includes(v)
  },
  variant: {
    type: String,
    default: 'gradient',
    validator: (v) => ['gradient', 'neutral', 'primary'].includes(v)
  },
  disabled: {
    type: Boolean,
    default: false
  },
  ariaLabel: {
    type: String,
    default: 'Rating scale'
  }
})

const emit = defineEmits(['update:modelValue'])

// Generate scale values
const scaleValues = computed(() => {
  const values = []
  for (let v = props.min; v <= props.max; v += props.step) {
    values.push(v)
  }
  return values
})

// Check if labels are provided for individual values
const hasIndividualLabels = computed(() => {
  return scaleValues.value.some(v => props.labels[v])
})

// Container classes
const containerClasses = computed(() => ({
  [`l-rating-scale--${props.size}`]: props.size !== 'default',
  [`l-rating-scale--${props.variant}`]: true,
  'l-rating-scale--disabled': props.disabled
}))

// Get button classes based on value and selection state
function getButtonClasses(value) {
  const isSelected = props.modelValue === value
  const range = props.max - props.min
  const position = (value - props.min) / range // 0 to 1

  return {
    'is-selected': isSelected,
    'is-low': position <= 0.3,
    'is-mid': position > 0.3 && position < 0.7,
    'is-high': position >= 0.7,
    'is-center': Math.abs(position - 0.5) < 0.1
  }
}

function selectValue(value) {
  if (props.disabled) return
  emit('update:modelValue', value)
}
</script>

<style scoped>
.l-rating-scale {
  display: flex;
  flex-direction: column;
  gap: 8px;
  user-select: none;
}

/* Scale Header (min/max labels) */
.scale-header {
  display: flex;
  justify-content: space-between;
  padding: 0 4px;
}

.scale-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.scale-label--min {
  color: var(--llars-success, #98d4bb);
}

.scale-label--max {
  color: var(--llars-danger, #e8a087);
}

/* Scale Buttons Container */
.scale-buttons {
  display: flex;
  gap: 5px;
  justify-content: center;
}

/* Individual Scale Button */
.scale-button {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 38px;
  height: 38px;
  padding: 6px 10px;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 8px 3px 8px 3px; /* Signature LLARS asymmetric style */
  background: rgba(var(--v-theme-on-surface), 0.03);
  cursor: pointer;
  transition: all 0.2s ease;
}

.scale-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
}

.scale-button:focus-visible {
  outline: 2px solid var(--llars-primary, #b0ca97);
  outline-offset: 2px;
}

.scale-button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

/* Scale Value Number */
.scale-value {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.8);
  transition: all 0.2s ease;
}

.scale-value-label {
  font-size: 0.6rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-align: center;
  max-width: 50px;
  line-height: 1.2;
}

/* Gradient Variant - Color-coded by position */
.l-rating-scale--gradient .scale-button.is-low {
  border-color: rgba(152, 212, 187, 0.4); /* Green tint */
}

.l-rating-scale--gradient .scale-button.is-low:hover:not(:disabled) {
  border-color: var(--llars-success, #98d4bb);
  background: rgba(152, 212, 187, 0.1);
}

.l-rating-scale--gradient .scale-button.is-mid {
  border-color: rgba(209, 188, 138, 0.4); /* Gold tint */
}

.l-rating-scale--gradient .scale-button.is-mid:hover:not(:disabled) {
  border-color: var(--llars-secondary, #D1BC8A);
  background: rgba(209, 188, 138, 0.1);
}

.l-rating-scale--gradient .scale-button.is-high {
  border-color: rgba(232, 160, 135, 0.4); /* Red tint */
}

.l-rating-scale--gradient .scale-button.is-high:hover:not(:disabled) {
  border-color: var(--llars-danger, #e8a087);
  background: rgba(232, 160, 135, 0.1);
}

/* Selected State - Gradient Variant */
.l-rating-scale--gradient .scale-button.is-selected.is-low {
  background: linear-gradient(135deg, #98d4bb 0%, #7dc4a8 100%);
  border-color: transparent;
  transform: scale(1.05);
}

.l-rating-scale--gradient .scale-button.is-selected.is-mid {
  background: linear-gradient(135deg, #D1BC8A 0%, #c4ad78 100%);
  border-color: transparent;
  transform: scale(1.05);
}

.l-rating-scale--gradient .scale-button.is-selected.is-high {
  background: linear-gradient(135deg, #e8a087 0%, #d88f75 100%);
  border-color: transparent;
  transform: scale(1.05);
}

.l-rating-scale--gradient .scale-button.is-selected .scale-value {
  color: white;
}

.l-rating-scale--gradient .scale-button.is-selected .scale-value-label {
  color: rgba(255, 255, 255, 0.9);
}

/* Primary Variant - All same color */
.l-rating-scale--primary .scale-button.is-selected {
  background: var(--llars-btn-primary-gradient, linear-gradient(135deg, #b0ca97, #9dba83));
  border-color: transparent;
  transform: scale(1.05);
}

.l-rating-scale--primary .scale-button.is-selected .scale-value {
  color: white;
}

/* Neutral Variant - Gray scale */
.l-rating-scale--neutral .scale-button.is-selected {
  background: rgba(var(--v-theme-on-surface), 0.8);
  border-color: transparent;
  transform: scale(1.05);
}

.l-rating-scale--neutral .scale-button.is-selected .scale-value {
  color: rgb(var(--v-theme-surface));
}

/* Size Variants */
.l-rating-scale--small .scale-button {
  min-width: 32px;
  height: 32px;
  padding: 4px 6px;
}

.l-rating-scale--small .scale-value {
  font-size: 0.8rem;
}

.l-rating-scale--large .scale-button {
  min-width: 48px;
  height: 48px;
  padding: 8px 14px;
}

.l-rating-scale--large .scale-value {
  font-size: 1.1rem;
}

/* Size Progression (middle items slightly larger) - disabled for compact design */
.scale-button.is-center {
  min-width: 40px;
  height: 40px;
}

.l-rating-scale--small .scale-button.is-center {
  min-width: 34px;
  height: 34px;
}

.l-rating-scale--large .scale-button.is-center {
  min-width: 52px;
  height: 52px;
}

/* Individual Labels Row */
.scale-labels-row {
  display: flex;
  justify-content: center;
  gap: 5px;
}

.scale-individual-label {
  min-width: 38px;
  text-align: center;
  font-size: 0.65rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  padding: 0 3px;
  transition: color 0.2s ease;
}

.scale-individual-label.is-selected {
  color: rgb(var(--v-theme-on-surface));
  font-weight: 500;
}

/* Disabled State */
.l-rating-scale--disabled {
  opacity: 0.6;
  pointer-events: none;
}

/* Responsive adjustments */
@media (max-width: 480px) {
  .scale-buttons {
    gap: 3px;
  }

  .scale-button {
    min-width: 34px;
    height: 34px;
    padding: 5px 7px;
  }

  .scale-value {
    font-size: 0.85rem;
  }

  .scale-button.is-center {
    min-width: 36px;
    height: 36px;
  }
}
</style>
