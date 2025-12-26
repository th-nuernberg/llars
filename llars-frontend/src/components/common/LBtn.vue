<template>
  <button
    v-bind="buttonAttrs"
    :class="buttonClasses"
    :disabled="disabled || loading"
    :aria-label="ariaLabel"
    @click="$emit('click', $event)"
  >
    <v-progress-circular
      v-if="loading"
      indeterminate
      size="18"
      width="2"
      class="mr-2"
    />
    <v-icon v-else-if="prependIcon" :icon="prependIcon" class="l-btn__icon l-btn__icon--prepend" />
    <span class="l-btn__content"><slot /></span>
    <v-icon v-if="appendIcon" :icon="appendIcon" class="l-btn__icon l-btn__icon--append" />
    <v-tooltip v-if="tooltipText" activator="parent" :location="tooltipLocation">
      {{ tooltipText }}
    </v-tooltip>
  </button>
</template>

<script setup>
/**
 * LBtn - LLARS Global Button Component
 *
 * A consistent, themeable button component with the signature LLARS styling.
 * Features the unique asymmetric border-radius: 16px 4px 16px 4px
 *
 * Variants:
 *   - primary: Main action (Sage Green #b0ca97)
 *   - secondary: Secondary action (Golden Beige #D1BC8A)
 *   - accent: Emphasis action (Soft Teal #88c4c8)
 *   - success: Success action (Soft Mint #98d4bb)
 *   - warning: Warning action (Soft Gold #e8c87a)
 *   - danger: Destructive action (Soft Coral #e8a087)
 *   - cancel: Neutral gray (#9e9e9e)
 *   - text: Text-only button
 *   - tonal: Subtle surface-variant background (Vuetify-like)
 *   - outlined: Outlined style
 *
 * Usage:
 *   <LBtn>Default Button</LBtn>
 *   <LBtn variant="primary">Primary Action</LBtn>
 *   <LBtn variant="secondary" prepend-icon="mdi-download">Download</LBtn>
 *   <LBtn variant="danger">Delete</LBtn>
 *   <LBtn variant="cancel">Cancel</LBtn>
 */
import { computed, useAttrs } from 'vue'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'secondary', 'accent', 'success', 'warning', 'danger', 'cancel', 'text', 'tonal', 'outlined'].includes(v)
  },
  size: {
    type: String,
    default: 'default',
    validator: (v) => ['small', 'default', 'large'].includes(v)
  },
  prependIcon: {
    type: String,
    default: null
  },
  appendIcon: {
    type: String,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  block: {
    type: Boolean,
    default: false
  },
  tooltip: {
    type: String,
    default: null
  },
  tooltipLocation: {
    type: String,
    default: 'bottom'
  }
})

defineEmits(['click'])

const attrs = useAttrs()
const tooltipText = computed(() => props.tooltip || attrs.title || attrs['aria-label'] || null)
const ariaLabel = computed(() => tooltipText.value || undefined)
const buttonAttrs = computed(() => {
  if (!tooltipText.value) return attrs
  const { title, ...rest } = attrs
  return rest
})

const buttonClasses = computed(() => ({
  'l-btn': true,
  [`l-btn--${props.variant}`]: true,
  [`l-btn--${props.size}`]: props.size !== 'default',
  'l-btn--block': props.block,
  'l-btn--loading': props.loading,
  'l-btn--disabled': props.disabled
}))
</script>

<style scoped>
/* Base Button Styles - LLARS Signature Design */
.l-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  min-height: 40px;
  border: none;
  border-radius: 16px 4px 16px 4px; /* Signature LLARS corner style */
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  text-transform: none;
  text-decoration: none;
  white-space: nowrap;
  transition: all 0.2s ease;
  color: white;
}

.l-btn:focus-visible {
  outline: 2px solid var(--llars-primary);
  outline-offset: 2px;
}

/* Icon Styling */
.l-btn__icon {
  font-size: 1.2em;
  line-height: 1;
}

.l-btn__icon--prepend {
  margin-right: 4px;
}

.l-btn__icon--append {
  margin-left: 4px;
}

/* Size Variants */
.l-btn--small {
  padding: 6px 12px;
  min-height: 32px;
  font-size: 0.85rem;
}

.l-btn--large {
  padding: 14px 24px;
  min-height: 48px;
  font-size: 1rem;
}

/* Block (Full Width) */
.l-btn--block {
  width: 100%;
}

/* States */
.l-btn--disabled,
.l-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

.l-btn--loading {
  cursor: wait;
}

/* ========================================
   VARIANT STYLES - Using CSS Custom Properties
   Automatically adapts to Light/Dark mode
   All buttons use subtle gradients for depth
   ======================================== */

/* Primary - Sage Green (Main Action) */
.l-btn--primary {
  background: var(--llars-btn-primary-gradient);
  color: white;
}

.l-btn--primary:hover:not(:disabled) {
  background: var(--llars-btn-primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.l-btn--primary:active:not(:disabled) {
  background: var(--llars-btn-primary-gradient);
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

/* Secondary - Golden Beige */
.l-btn--secondary {
  background: var(--llars-btn-secondary-gradient);
  color: white;
}

.l-btn--secondary:hover:not(:disabled) {
  background: var(--llars-btn-secondary-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.l-btn--secondary:active:not(:disabled) {
  background: var(--llars-btn-secondary-gradient);
  transform: translateY(0);
}

/* Accent - Soft Teal */
.l-btn--accent {
  background: var(--llars-btn-accent-gradient);
  color: white;
}

.l-btn--accent:hover:not(:disabled) {
  background: var(--llars-btn-accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.l-btn--accent:active:not(:disabled) {
  background: var(--llars-btn-accent-gradient);
  transform: translateY(0);
}

/* Success - Soft Mint */
.l-btn--success {
  background: var(--llars-btn-success-gradient);
  color: white;
}

.l-btn--success:hover:not(:disabled) {
  background: var(--llars-btn-success-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.l-btn--success:active:not(:disabled) {
  background: var(--llars-btn-success-gradient);
  transform: translateY(0);
}

/* Warning - Soft Gold */
.l-btn--warning {
  background: var(--llars-btn-warning-gradient);
  color: white;
}

.l-btn--warning:hover:not(:disabled) {
  background: var(--llars-btn-warning-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.l-btn--warning:active:not(:disabled) {
  background: var(--llars-btn-warning-gradient);
  transform: translateY(0);
}

/* Danger - Soft Coral */
.l-btn--danger {
  background: var(--llars-btn-danger-gradient);
  color: white;
}

.l-btn--danger:hover:not(:disabled) {
  background: var(--llars-btn-danger-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.l-btn--danger:active:not(:disabled) {
  background: var(--llars-btn-danger-gradient);
  transform: translateY(0);
}

/* Cancel - Neutral Gray */
.l-btn--cancel {
  background: var(--llars-btn-cancel-gradient);
  color: white;
}

.l-btn--cancel:hover:not(:disabled) {
  background: var(--llars-btn-cancel-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.l-btn--cancel:active:not(:disabled) {
  background: var(--llars-btn-cancel-gradient);
  transform: translateY(0);
}

/* Text - No Background */
.l-btn--text {
  background-color: transparent;
  color: rgb(var(--v-theme-on-surface));
  padding: 10px 12px;
}

.l-btn--text:hover:not(:disabled) {
  background-color: rgba(var(--v-theme-on-surface), 0.08);
}

.l-btn--text:active:not(:disabled) {
  background-color: rgba(var(--v-theme-on-surface), 0.12);
}

/* Tonal - Subtle surface background (theme-aware) */
.l-btn--tonal {
  background-color: rgba(var(--v-theme-surface-variant), 0.6);
  color: rgb(var(--v-theme-on-surface));
}

.l-btn--tonal:hover:not(:disabled) {
  background-color: rgba(var(--v-theme-surface-variant), 0.8);
  transform: translateY(-1px);
}

.l-btn--tonal:active:not(:disabled) {
  background-color: rgba(var(--v-theme-surface-variant), 0.9);
  transform: translateY(0);
}

/* Outlined */
.l-btn--outlined {
  background-color: transparent;
  color: var(--llars-primary);
  border: 2px solid var(--llars-primary);
}

.l-btn--outlined:hover:not(:disabled) {
  background-color: rgba(var(--v-theme-on-surface), 0.05);
  transform: translateY(-1px);
}

.l-btn--outlined:active:not(:disabled) {
  background-color: rgba(var(--v-theme-on-surface), 0.1);
}
</style>
