<template>
  <button
    :class="buttonClasses"
    :disabled="disabled || loading"
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
 *   - outlined: Outlined style
 *
 * Usage:
 *   <LBtn>Default Button</LBtn>
 *   <LBtn variant="primary">Primary Action</LBtn>
 *   <LBtn variant="secondary" prepend-icon="mdi-download">Download</LBtn>
 *   <LBtn variant="danger">Delete</LBtn>
 *   <LBtn variant="cancel">Cancel</LBtn>
 */
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'secondary', 'accent', 'success', 'warning', 'danger', 'cancel', 'text', 'outlined'].includes(v)
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
  }
})

defineEmits(['click'])

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
   ======================================== */

/* Primary - Sage Green (Main Action) */
.l-btn--primary {
  background-color: var(--llars-primary);
  color: white;
}

.l-btn--primary:hover:not(:disabled) {
  background-color: var(--llars-primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.l-btn--primary:active:not(:disabled) {
  background-color: var(--llars-primary-active);
  transform: translateY(0);
}

/* Secondary - Golden Beige */
.l-btn--secondary {
  background-color: var(--llars-secondary);
  color: white;
}

.l-btn--secondary:hover:not(:disabled) {
  background-color: var(--llars-secondary-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.l-btn--secondary:active:not(:disabled) {
  background-color: var(--llars-secondary-active);
}

/* Accent - Soft Teal */
.l-btn--accent {
  background-color: var(--llars-accent);
  color: white;
}

.l-btn--accent:hover:not(:disabled) {
  background-color: var(--llars-accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.l-btn--accent:active:not(:disabled) {
  background-color: var(--llars-accent-active);
}

/* Success - Soft Mint */
.l-btn--success {
  background-color: var(--llars-success);
  color: white;
}

.l-btn--success:hover:not(:disabled) {
  background-color: var(--llars-success-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.l-btn--success:active:not(:disabled) {
  background-color: var(--llars-success-active);
}

/* Warning - Soft Gold */
.l-btn--warning {
  background-color: var(--llars-warning);
  color: white;
}

.l-btn--warning:hover:not(:disabled) {
  background-color: var(--llars-warning-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.l-btn--warning:active:not(:disabled) {
  background-color: var(--llars-warning-active);
}

/* Danger - Soft Coral */
.l-btn--danger {
  background-color: var(--llars-danger);
  color: white;
}

.l-btn--danger:hover:not(:disabled) {
  background-color: var(--llars-danger-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.l-btn--danger:active:not(:disabled) {
  background-color: var(--llars-danger-active);
}

/* Cancel - Neutral Gray */
.l-btn--cancel {
  background-color: var(--llars-gray);
  color: white;
}

.l-btn--cancel:hover:not(:disabled) {
  background-color: var(--llars-gray-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.l-btn--cancel:active:not(:disabled) {
  background-color: var(--llars-gray-active);
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
