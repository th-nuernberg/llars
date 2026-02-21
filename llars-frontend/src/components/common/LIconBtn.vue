<template>
  <v-btn
    v-bind="buttonProps"
    :class="buttonClasses"
    :aria-label="ariaLabel"
    :data-matomo-name="matomoName"
    @click="$emit('click', $event)"
  >
    <LIcon :icon="icon" :size="iconSize" />
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
import { computed, useAttrs } from 'vue'

const attrs = useAttrs()

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
  variant: 'text',
  size: props.size,
  color: variantColors[props.variant],
  loading: props.loading,
  disabled: props.disabled,
  // Don't use icon: true - we want custom LLARS styling, not circular
  minWidth: 0
}))

const buttonClasses = computed(() => ({
  'l-icon-btn': true,
  [`l-icon-btn--${props.variant}`]: true
}))

const matomoName = computed(() => {
  const explicit =
    attrs['data-matomo-name'] ||
    attrs['data-track'] ||
    attrs['data-testid'] ||
    attrs['aria-label'] ||
    attrs['title']

  if (explicit) return String(explicit)
  if (props.tooltip) return String(props.tooltip)
  return String(props.icon)
})

const ariaLabel = computed(() => {
  const explicit = attrs['aria-label'] || attrs['title']
  if (explicit) return String(explicit)
  if (props.tooltip) return String(props.tooltip)
  return String(props.icon)
})
</script>

<style scoped>
.l-icon-btn {
  /* LLARS signature asymmetric border-radius (smaller version for icon buttons) */
  border-radius: 8px 2px 8px 2px !important;
  transition: all 0.2s ease;
  /* Square dimensions for icon button */
  padding: 6px !important;
  min-width: 32px !important;
  width: 32px;
  height: 32px;
}

/* Size variants */
.l-icon-btn.v-btn--size-x-small {
  min-width: 24px !important;
  width: 24px;
  height: 24px;
  padding: 4px !important;
  border-radius: 6px 2px 6px 2px !important;
}

.l-icon-btn.v-btn--size-small {
  min-width: 32px !important;
  width: 32px;
  height: 32px;
  padding: 6px !important;
}

.l-icon-btn.v-btn--size-default {
  min-width: 40px !important;
  width: 40px;
  height: 40px;
  padding: 8px !important;
  border-radius: 10px 3px 10px 3px !important;
}

.l-icon-btn.v-btn--size-large {
  min-width: 48px !important;
  width: 48px;
  height: 48px;
  padding: 10px !important;
  border-radius: 12px 3px 12px 3px !important;
}

.l-icon-btn.v-btn--size-x-large {
  min-width: 56px !important;
  width: 56px;
  height: 56px;
  padding: 12px !important;
  border-radius: 14px 4px 14px 4px !important;
}

.l-icon-btn:hover:not(:disabled) {
  transform: scale(1.05);
}

.l-icon-btn:active:not(:disabled) {
  transform: scale(0.95);
}

/* Variant-specific hover effects with LLARS asymmetric shape */
.l-icon-btn--default:hover:not(:disabled) {
  background-color: rgba(var(--v-theme-on-surface), 0.08);
}

.l-icon-btn--primary:hover:not(:disabled) {
  background-color: rgba(var(--v-theme-primary), 0.15);
}

.l-icon-btn--danger:hover:not(:disabled) {
  background-color: rgba(var(--v-theme-error), 0.15);
}

.l-icon-btn--success:hover:not(:disabled) {
  background-color: rgba(var(--v-theme-success), 0.15);
}

.l-icon-btn--warning:hover:not(:disabled) {
  background-color: rgba(var(--v-theme-warning), 0.15);
}
</style>
