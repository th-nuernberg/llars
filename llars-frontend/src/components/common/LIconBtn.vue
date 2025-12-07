<template>
  <v-btn
    v-bind="buttonProps"
    :class="buttonClasses"
    @click="$emit('click', $event)"
  >
    <v-icon :icon="icon" :size="iconSize" />
    <v-tooltip v-if="tooltip" activator="parent" :location="tooltipLocation">
      {{ tooltip }}
    </v-tooltip>
  </v-btn>
</template>

<script setup>
/**
 * LIconBtn - LLARS Global Icon Button Component
 *
 * A consistent icon-only button for actions in tables, toolbars, etc.
 *
 * Usage:
 *   <LIconBtn icon="mdi-pencil" tooltip="Bearbeiten" />
 *   <LIconBtn icon="mdi-delete" variant="danger" tooltip="Löschen" />
 *   <LIconBtn icon="mdi-chart-bar" variant="primary" tooltip="Statistiken" />
 */
import { computed } from 'vue'

const props = defineProps({
  /**
   * Icon (mdi-* format) - required
   */
  icon: {
    type: String,
    required: true
  },

  /**
   * Button variant style
   * - default: Text button (no background)
   * - primary: Primary color on hover
   * - danger: Error/red color
   * - success: Success/green color
   * - warning: Warning/orange color
   */
  variant: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'primary', 'danger', 'success', 'warning'].includes(v)
  },

  /**
   * Button size
   */
  size: {
    type: String,
    default: 'small',
    validator: (v) => ['x-small', 'small', 'default', 'large', 'x-large'].includes(v)
  },

  /**
   * Tooltip text
   */
  tooltip: {
    type: String,
    default: null
  },

  /**
   * Tooltip location
   */
  tooltipLocation: {
    type: String,
    default: 'top'
  },

  /**
   * Loading state
   */
  loading: {
    type: Boolean,
    default: false
  },

  /**
   * Disabled state
   */
  disabled: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])

// Map variants to colors
const variantColors = {
  default: undefined,
  primary: 'primary',
  danger: 'error',
  success: 'success',
  warning: 'warning'
}

// Icon sizes based on button size
const iconSizes = {
  'x-small': 16,
  'small': 20,
  'default': 24,
  'large': 28,
  'x-large': 32
}

const iconSize = computed(() => iconSizes[props.size] || 20)

const buttonProps = computed(() => ({
  icon: true,
  variant: 'text',
  size: props.size,
  color: variantColors[props.variant],
  loading: props.loading,
  disabled: props.disabled
}))

const buttonClasses = computed(() => ({
  'l-icon-btn': true,
  [`l-icon-btn--${props.variant}`]: true
}))
</script>

<style scoped>
.l-icon-btn {
  transition: all 0.2s ease;
}

.l-icon-btn:hover:not(:disabled) {
  transform: scale(1.1);
}

.l-icon-btn:active:not(:disabled) {
  transform: scale(0.95);
}

/* Variant-specific hover effects */
.l-icon-btn--default:hover:not(:disabled) {
  background-color: rgba(var(--v-theme-on-surface), 0.08);
}

.l-icon-btn--primary:hover:not(:disabled) {
  background-color: rgba(var(--v-theme-primary), 0.12);
}

.l-icon-btn--danger:hover:not(:disabled) {
  background-color: rgba(var(--v-theme-error), 0.12);
}

.l-icon-btn--success:hover:not(:disabled) {
  background-color: rgba(var(--v-theme-success), 0.12);
}

.l-icon-btn--warning:hover:not(:disabled) {
  background-color: rgba(var(--v-theme-warning), 0.12);
}
</style>
