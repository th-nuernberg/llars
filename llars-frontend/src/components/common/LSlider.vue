<template>
  <div
    class="l-slider"
    :class="{
      'l-slider--active': isActive,
      'l-slider--touched': hasBeenTouched
    }"
  >
    <v-slider
      v-bind="sliderProps"
      :model-value="modelValue"
      :color="sliderColor"
      :track-color="trackColor"
      :thumb-color="sliderColor"
      @update:model-value="handleUpdate"
      @mousedown="handleInteraction"
      @touchstart="handleInteraction"
      @focus="handleInteraction"
    >
      <template v-if="$slots['thumb-label']" #thumb-label="slotProps">
        <slot name="thumb-label" v-bind="slotProps" />
      </template>
      <template v-if="$slots['prepend']" #prepend>
        <slot name="prepend" />
      </template>
      <template v-if="$slots['append']" #append>
        <slot name="append" />
      </template>
    </v-slider>
  </div>
</template>

<script setup>
/**
 * LSlider - LLARS Global Slider Component
 *
 * A slider that transitions from gray to a color gradient based on value.
 * Low values = red, medium = yellow, high values = green.
 *
 * Usage:
 *   <LSlider v-model="confidence" :min="0" :max="100" />
 *   <LSlider v-model="rating" :min="1" :max="5" color-mode="fixed" color="primary" />
 */
import { ref, computed, watch, useAttrs } from 'vue'

const attrs = useAttrs()

const props = defineProps({
  /**
   * v-model value
   */
  modelValue: {
    type: Number,
    default: 50
  },

  /**
   * Minimum value
   */
  min: {
    type: Number,
    default: 0
  },

  /**
   * Maximum value
   */
  max: {
    type: Number,
    default: 100
  },

  /**
   * Step increment
   */
  step: {
    type: Number,
    default: 1
  },

  /**
   * Color mode:
   * - 'gradient': Red to green based on value (default)
   * - 'fixed': Use a fixed color
   */
  colorMode: {
    type: String,
    default: 'gradient',
    validator: (v) => ['gradient', 'fixed'].includes(v)
  },

  /**
   * Fixed color (only used when colorMode is 'fixed')
   */
  color: {
    type: String,
    default: 'primary'
  },

  /**
   * Show thumb label
   */
  thumbLabel: {
    type: [Boolean, String],
    default: true
  },

  /**
   * Start as active (colored) immediately
   */
  startActive: {
    type: Boolean,
    default: false
  },

  /**
   * Density
   */
  density: {
    type: String,
    default: 'default'
  },

  /**
   * Disabled state
   */
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'change', 'touched'])

// Track if user has interacted with slider
const hasBeenTouched = ref(props.startActive)
const isActive = ref(false)

// Calculate normalized value (0-1)
const normalizedValue = computed(() => {
  const range = props.max - props.min
  if (range === 0) return 0.5
  return (props.modelValue - props.min) / range
})

// Calculate gradient color based on value
// 0 = red (#e57373), 0.5 = yellow (#e8c87a), 1 = green (#4CAF50)
const gradientColor = computed(() => {
  const value = normalizedValue.value

  // Colors: red (danger) -> yellow (warning) -> green (success)
  const red = { r: 229, g: 115, b: 115 }    // #e57373 (stronger red)
  const yellow = { r: 232, g: 200, b: 122 } // #e8c87a (warning)
  const green = { r: 76, g: 175, b: 80 }    // #4CAF50 (vibrant green)

  let r, g, b

  if (value <= 0.5) {
    // Interpolate between red and yellow
    const t = value * 2
    r = Math.round(red.r + (yellow.r - red.r) * t)
    g = Math.round(red.g + (yellow.g - red.g) * t)
    b = Math.round(red.b + (yellow.b - red.b) * t)
  } else {
    // Interpolate between yellow and green
    const t = (value - 0.5) * 2
    r = Math.round(yellow.r + (green.r - yellow.r) * t)
    g = Math.round(yellow.g + (green.g - yellow.g) * t)
    b = Math.round(yellow.b + (green.b - yellow.b) * t)
  }

  return `rgb(${r}, ${g}, ${b})`
})

// Determine slider color
const sliderColor = computed(() => {
  if (!hasBeenTouched.value) {
    return 'grey'
  }

  if (props.colorMode === 'fixed') {
    return props.color
  }

  return gradientColor.value
})

// Track color (background of unfilled portion)
const trackColor = computed(() => {
  if (!hasBeenTouched.value) {
    return 'grey-lighten-2'
  }
  return 'grey-lighten-3'
})

// Props to pass to v-slider
const sliderProps = computed(() => ({
  min: props.min,
  max: props.max,
  step: props.step,
  thumbLabel: props.thumbLabel,
  density: props.density,
  disabled: props.disabled,
  hideDetails: attrs.hideDetails ?? true
}))

function handleUpdate(value) {
  emit('update:modelValue', value)
  emit('change', value)
}

function handleInteraction() {
  if (!hasBeenTouched.value) {
    hasBeenTouched.value = true
    emit('touched')
  }
  isActive.value = true
}

// Reset active state when mouse/touch ends
if (typeof window !== 'undefined') {
  const handleEnd = () => {
    isActive.value = false
  }
  window.addEventListener('mouseup', handleEnd)
  window.addEventListener('touchend', handleEnd)
}

// Watch for external value changes - if value changes from initial, mark as touched
watch(() => props.modelValue, (newVal, oldVal) => {
  if (newVal !== oldVal && !hasBeenTouched.value) {
    // Value changed externally, mark as touched
    hasBeenTouched.value = true
  }
})
</script>

<style scoped>
.l-slider {
  transition: all 0.3s ease;
}

/* Smooth color transition on the slider */
.l-slider :deep(.v-slider-track__fill) {
  transition: background-color 0.3s ease !important;
}

.l-slider :deep(.v-slider-thumb) {
  transition: background-color 0.3s ease, box-shadow 0.15s ease !important;
}

.l-slider :deep(.v-slider-track__background) {
  transition: background-color 0.3s ease !important;
}

/* Active state - highlight with shadow instead of scale to keep centered */
.l-slider--active :deep(.v-slider-thumb) {
  box-shadow: 0 0 0 4px rgba(var(--v-theme-on-surface), 0.12), 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* Touched state - add subtle glow */
.l-slider--touched :deep(.v-slider-thumb) {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* LLARS asymmetric border-radius for thumb */
.l-slider :deep(.v-slider-thumb__surface) {
  border-radius: 8px 2px 8px 2px !important;
}

/* Track styling */
.l-slider :deep(.v-slider-track) {
  border-radius: 4px 1px 4px 1px;
}

.l-slider :deep(.v-slider-track__fill) {
  border-radius: 4px 1px 4px 1px;
}

.l-slider :deep(.v-slider-track__background) {
  border-radius: 4px 1px 4px 1px;
}
</style>
