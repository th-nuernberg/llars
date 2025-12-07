<template>
  <v-btn
    v-bind="buttonProps"
    :class="buttonClasses"
    @click="$emit('click', $event)"
  >
    <v-icon v-if="prependIcon" :icon="prependIcon" class="mr-2" />
    <slot />
    <v-icon v-if="appendIcon" :icon="appendIcon" class="ml-2" />
  </v-btn>
</template>

<script setup>
/**
 * LBtn - LLARS Global Button Component
 *
 * A consistent, themeable button component for the entire application.
 * Wraps Vuetify's v-btn with standardized styling and variants.
 *
 * Usage:
 *   <LBtn>Default Button</LBtn>
 *   <LBtn variant="primary">Primary Action</LBtn>
 *   <LBtn variant="secondary">Secondary Action</LBtn>
 *   <LBtn variant="danger">Delete</LBtn>
 *   <LBtn variant="success" prepend-icon="mdi-check">Confirm</LBtn>
 *   <LBtn variant="text">Cancel</LBtn>
 */
import { computed } from 'vue'

const props = defineProps({
  /**
   * Button variant style
   * - primary: Main action button (filled, primary color)
   * - secondary: Secondary action (outlined, primary color)
   * - success: Positive action (filled, success color)
   * - danger: Destructive action (filled, error color)
   * - warning: Caution action (filled, warning color)
   * - text: Text-only button (no background)
   * - tonal: Subtle filled button
   */
  variant: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'secondary', 'success', 'danger', 'warning', 'text', 'tonal'].includes(v)
  },

  /**
   * Button size
   */
  size: {
    type: String,
    default: 'default',
    validator: (v) => ['x-small', 'small', 'default', 'large', 'x-large'].includes(v)
  },

  /**
   * Prepend icon (mdi-* format)
   */
  prependIcon: {
    type: String,
    default: null
  },

  /**
   * Append icon (mdi-* format)
   */
  appendIcon: {
    type: String,
    default: null
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
  },

  /**
   * Block (full-width) button
   */
  block: {
    type: Boolean,
    default: false
  },

  /**
   * Rounded corners
   */
  rounded: {
    type: [Boolean, String],
    default: 'lg'
  },

  /**
   * Elevation (shadow depth)
   */
  elevation: {
    type: [Number, String],
    default: 0
  }
})

defineEmits(['click'])

// Map our variants to Vuetify props
const variantMapping = {
  primary: { color: 'primary', variant: 'flat' },
  secondary: { color: 'primary', variant: 'outlined' },
  success: { color: 'success', variant: 'flat' },
  danger: { color: 'error', variant: 'flat' },
  warning: { color: 'warning', variant: 'flat' },
  text: { color: undefined, variant: 'text' },
  tonal: { color: 'primary', variant: 'tonal' }
}

const buttonProps = computed(() => {
  const mapping = variantMapping[props.variant] || variantMapping.primary

  return {
    color: mapping.color,
    variant: mapping.variant,
    size: props.size,
    loading: props.loading,
    disabled: props.disabled,
    block: props.block,
    rounded: props.rounded,
    elevation: props.elevation
  }
})

const buttonClasses = computed(() => ({
  'l-btn': true,
  [`l-btn--${props.variant}`]: true
}))
</script>

<style scoped>
.l-btn {
  font-weight: 500;
  letter-spacing: 0.03em;
  text-transform: none;
  transition: all 0.2s ease;
}

.l-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.l-btn:active:not(:disabled) {
  transform: translateY(0);
}

/* Primary variant - enhanced styling */
.l-btn--primary {
  box-shadow: 0 2px 4px rgba(var(--v-theme-primary), 0.2);
}

.l-btn--primary:hover:not(:disabled) {
  box-shadow: 0 4px 8px rgba(var(--v-theme-primary), 0.3);
}

/* Secondary variant */
.l-btn--secondary {
  border-width: 2px;
}

/* Danger variant */
.l-btn--danger {
  box-shadow: 0 2px 4px rgba(var(--v-theme-error), 0.2);
}

.l-btn--danger:hover:not(:disabled) {
  box-shadow: 0 4px 8px rgba(var(--v-theme-error), 0.3);
}

/* Success variant */
.l-btn--success {
  box-shadow: 0 2px 4px rgba(var(--v-theme-success), 0.2);
}

.l-btn--success:hover:not(:disabled) {
  box-shadow: 0 4px 8px rgba(var(--v-theme-success), 0.3);
}
</style>
