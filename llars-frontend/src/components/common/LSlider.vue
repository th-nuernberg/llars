<template>
  <div
    class="l-slider"
    :class="{
      'l-slider--inactive': !hasBeenTouched && !isHovering && !isActive,
      'l-slider--hovering': isHovering && !hasBeenTouched && !isActive,
      'l-slider--active': isActive,
      'l-slider--touched': hasBeenTouched
    }"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <v-slider
      v-bind="sliderProps"
      :model-value="modelValue"
      :color="sliderColor"
      :track-color="trackColor"
      :thumb-color="thumbColor"
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

// Track interaction states
const hasBeenTouched = ref(props.startActive)
const isActive = ref(false)
const isHovering = ref(false)

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

// Determine slider fill color
const sliderColor = computed(() => {
  // Active or touched = full color
  if (hasBeenTouched.value || isActive.value) {
    if (props.colorMode === 'fixed') {
      return props.color
    }
    return gradientColor.value
  }

  // Hovering but not touched = hint of color (handled by CSS animation)
  // Return grey, the CSS will handle the shimmer
  return 'grey'
})

// Determine thumb color (separate for hover effect)
const thumbColor = computed(() => {
  // Active or touched = full color
  if (hasBeenTouched.value || isActive.value) {
    if (props.colorMode === 'fixed') {
      return props.color
    }
    return gradientColor.value
  }

  // Grey when inactive
  return 'grey'
})

// Track color (background of unfilled portion)
const trackColor = computed(() => {
  if (hasBeenTouched.value || isActive.value) {
    return 'grey-lighten-3'
  }
  return 'grey-lighten-2'
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

function handleMouseEnter() {
  isHovering.value = true
}

function handleMouseLeave() {
  isHovering.value = false
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
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ============================================
   Base Transitions - Smooth everywhere
   ============================================ */
.l-slider :deep(.v-slider-track__fill) {
  transition: background-color 0.5s cubic-bezier(0.4, 0, 0.2, 1),
              opacity 0.3s ease !important;
}

.l-slider :deep(.v-slider-thumb) {
  transition: background-color 0.5s cubic-bezier(0.4, 0, 0.2, 1),
              box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1),
              transform 0.2s ease !important;
}

.l-slider :deep(.v-slider-thumb__surface) {
  transition: background-color 0.5s cubic-bezier(0.4, 0, 0.2, 1),
              box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.l-slider :deep(.v-slider-track__background) {
  transition: background-color 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* ============================================
   Inactive State - Gray and muted
   ============================================ */
.l-slider--inactive :deep(.v-slider-track__fill) {
  opacity: 0.6;
}

.l-slider--inactive :deep(.v-slider-thumb__surface) {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* ============================================
   Hovering State - Shimmer animation
   ============================================ */
.l-slider--hovering :deep(.v-slider-thumb__surface) {
  animation: shimmer 2s ease-in-out infinite;
  box-shadow: 0 0 12px rgba(176, 202, 151, 0.4),
              0 0 20px rgba(136, 196, 200, 0.3);
}

.l-slider--hovering :deep(.v-slider-track__fill) {
  animation: trackShimmer 2s ease-in-out infinite;
  opacity: 0.8;
}

@keyframes shimmer {
  0% {
    box-shadow: 0 0 8px rgba(176, 202, 151, 0.3),
                0 0 16px rgba(136, 196, 200, 0.2);
    background-color: #9e9e9e;
  }
  33% {
    box-shadow: 0 0 12px rgba(136, 196, 200, 0.5),
                0 0 24px rgba(176, 202, 151, 0.3);
    background-color: #a8b8a0;
  }
  66% {
    box-shadow: 0 0 12px rgba(209, 188, 138, 0.5),
                0 0 24px rgba(136, 196, 200, 0.3);
    background-color: #a0b8b8;
  }
  100% {
    box-shadow: 0 0 8px rgba(176, 202, 151, 0.3),
                0 0 16px rgba(136, 196, 200, 0.2);
    background-color: #9e9e9e;
  }
}

@keyframes trackShimmer {
  0% {
    background-color: #9e9e9e;
  }
  33% {
    background-color: #a8b8a0;
  }
  66% {
    background-color: #a0b8b8;
  }
  100% {
    background-color: #9e9e9e;
  }
}

/* ============================================
   Active State - Grabbing the slider
   ============================================ */
.l-slider--active :deep(.v-slider-thumb) {
  transform: scale(1.1);
}

.l-slider--active :deep(.v-slider-thumb__surface) {
  box-shadow: 0 0 0 4px rgba(var(--v-theme-primary), 0.2),
              0 4px 12px rgba(0, 0, 0, 0.25) !important;
  animation: none !important;
}

.l-slider--active :deep(.v-slider-track__fill) {
  opacity: 1 !important;
  animation: none !important;
}

/* ============================================
   Touched State - Has been interacted with
   ============================================ */
.l-slider--touched :deep(.v-slider-thumb__surface) {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  animation: none !important;
}

.l-slider--touched :deep(.v-slider-track__fill) {
  opacity: 1;
  animation: none !important;
}

/* ============================================
   LLARS Design - Asymmetric border-radius
   ============================================ */
.l-slider :deep(.v-slider-thumb__surface) {
  border-radius: 8px 2px 8px 2px !important;
}

.l-slider :deep(.v-slider-track) {
  border-radius: 4px 1px 4px 1px;
}

.l-slider :deep(.v-slider-track__fill) {
  border-radius: 4px 1px 4px 1px;
}

.l-slider :deep(.v-slider-track__background) {
  border-radius: 4px 1px 4px 1px;
}

/* ============================================
   Dark Mode Adjustments
   ============================================ */
.v-theme--dark .l-slider--hovering :deep(.v-slider-thumb__surface) {
  animation: shimmerDark 2s ease-in-out infinite;
}

.v-theme--dark .l-slider--hovering :deep(.v-slider-track__fill) {
  animation: trackShimmerDark 2s ease-in-out infinite;
}

@keyframes shimmerDark {
  0% {
    box-shadow: 0 0 8px rgba(90, 107, 74, 0.4),
                0 0 16px rgba(74, 122, 125, 0.3);
    background-color: #6a6a6a;
  }
  33% {
    box-shadow: 0 0 12px rgba(74, 122, 125, 0.6),
                0 0 24px rgba(90, 107, 74, 0.4);
    background-color: #5a6a5a;
  }
  66% {
    box-shadow: 0 0 12px rgba(138, 122, 85, 0.6),
                0 0 24px rgba(74, 122, 125, 0.4);
    background-color: #5a6a6a;
  }
  100% {
    box-shadow: 0 0 8px rgba(90, 107, 74, 0.4),
                0 0 16px rgba(74, 122, 125, 0.3);
    background-color: #6a6a6a;
  }
}

@keyframes trackShimmerDark {
  0% {
    background-color: #6a6a6a;
  }
  33% {
    background-color: #5a6a5a;
  }
  66% {
    background-color: #5a6a6a;
  }
  100% {
    background-color: #6a6a6a;
  }
}
</style>
