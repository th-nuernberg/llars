<template>
  <label
    class="l-checkbox"
    :class="[
      `l-checkbox--size-${size}`,
      {
        'l-checkbox--checked': isChecked,
        'l-checkbox--disabled': disabled,
        'l-checkbox--error': error
      }
    ]"
  >
    <input
      type="checkbox"
      :checked="isChecked"
      :disabled="disabled"
      :value="value"
      class="l-checkbox__input"
      @change="handleChange"
    />
    <span class="l-checkbox__box" :class="{ 'l-checkbox__box--animating': isAnimating }">
      <svg class="l-checkbox__checkmark" viewBox="0 0 24 24">
        <path
          class="l-checkbox__checkmark-path"
          d="M4.5 12.5L9.5 17.5L19.5 6.5"
          fill="none"
          stroke="currentColor"
          stroke-width="3"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </span>
    <span v-if="$slots.default || label" class="l-checkbox__label">
      <slot>{{ label }}</slot>
    </span>
  </label>
</template>

<script setup>
/**
 * LCheckbox - LLARS Global Checkbox Component
 *
 * A custom checkbox with the signature LLARS asymmetric border-radius styling.
 * Features an animated checkmark on selection.
 *
 * Props:
 *   - size: 'x-small' (14px) | 'small' (18px) | 'default' (22px) | 'large' (28px)
 *
 * Usage:
 *   <LCheckbox v-model="agreed" label="I agree to terms" />
 *   <LCheckbox v-model="items" value="item1">Item 1</LCheckbox>
 *   <LCheckbox v-model="enabled" color="success" />
 *   <LCheckbox v-model="compact" size="x-small" />
 */
import { computed, ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: [Boolean, Array],
    default: false
  },
  value: {
    type: [String, Number, Boolean, Object],
    default: true
  },
  label: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  error: {
    type: Boolean,
    default: false
  },
  color: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'secondary', 'accent', 'success', 'warning', 'danger'].includes(v)
  },
  size: {
    type: String,
    default: 'default',
    validator: (v) => ['x-small', 'small', 'default', 'large'].includes(v)
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const isAnimating = ref(false)

const isChecked = computed(() => {
  if (Array.isArray(props.modelValue)) {
    return props.modelValue.includes(props.value)
  }
  return props.modelValue === true || props.modelValue === props.value
})

function handleChange(event) {
  if (props.disabled) return

  // Trigger animation
  isAnimating.value = true
  setTimeout(() => {
    isAnimating.value = false
  }, 300)

  let newValue
  if (Array.isArray(props.modelValue)) {
    newValue = [...props.modelValue]
    if (event.target.checked) {
      newValue.push(props.value)
    } else {
      const index = newValue.indexOf(props.value)
      if (index > -1) newValue.splice(index, 1)
    }
  } else {
    newValue = event.target.checked
  }

  emit('update:modelValue', newValue)
  emit('change', newValue)
}

// Watch for external changes to trigger animation
let lastChecked = isChecked.value
watch(isChecked, (newVal) => {
  if (newVal !== lastChecked) {
    isAnimating.value = true
    setTimeout(() => {
      isAnimating.value = false
    }, 300)
    lastChecked = newVal
  }
})
</script>

<style scoped>
.l-checkbox {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.l-checkbox__input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
  pointer-events: none;
}

.l-checkbox__box {
  position: relative;
  width: 22px;
  height: 22px;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.4);
  border-radius: 6px 2px 6px 2px; /* LLARS signature asymmetric corners */
  background-color: transparent;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.l-checkbox:hover:not(.l-checkbox--disabled) .l-checkbox__box {
  border-color: var(--llars-primary);
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.l-checkbox--checked .l-checkbox__box {
  border-color: var(--llars-primary);
  background-color: var(--llars-primary);
}

.l-checkbox--checked:hover:not(.l-checkbox--disabled) .l-checkbox__box {
  background-color: var(--llars-primary-dark, #9ab882);
}

/* Checkmark */
.l-checkbox__checkmark {
  width: 16px;
  height: 16px;
  color: white;
  opacity: 0;
  transform: scale(0.5);
  transition: all 0.2s ease;
}

.l-checkbox--checked .l-checkbox__checkmark {
  opacity: 1;
  transform: scale(1);
}

/* Checkmark path animation */
.l-checkbox__checkmark-path {
  stroke-dasharray: 30;
  stroke-dashoffset: 30;
  transition: stroke-dashoffset 0.3s ease;
}

.l-checkbox--checked .l-checkbox__checkmark-path {
  stroke-dashoffset: 0;
}

/* Animation on click */
.l-checkbox__box--animating {
  animation: checkbox-pop 0.3s ease;
}

@keyframes checkbox-pop {
  0% { transform: scale(1); }
  50% { transform: scale(1.15); }
  100% { transform: scale(1); }
}

/* Label */
.l-checkbox__label {
  font-size: 0.9rem;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.4;
}

/* Disabled state */
.l-checkbox--disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.l-checkbox--disabled .l-checkbox__box {
  background-color: rgba(var(--v-theme-on-surface), 0.08);
}

/* Error state */
.l-checkbox--error .l-checkbox__box {
  border-color: var(--llars-danger, #e8a087);
}

.l-checkbox--error .l-checkbox__label {
  color: var(--llars-danger, #e8a087);
}

/* Focus visible */
.l-checkbox__input:focus-visible + .l-checkbox__box {
  outline: 2px solid var(--llars-primary);
  outline-offset: 2px;
}

/* Size variants */
/* X-Small: 14px */
.l-checkbox--size-x-small .l-checkbox__box {
  width: 14px;
  height: 14px;
  border-width: 1.5px;
  border-radius: 4px 1px 4px 1px;
}

.l-checkbox--size-x-small .l-checkbox__checkmark {
  width: 10px;
  height: 10px;
}

.l-checkbox--size-x-small .l-checkbox__label {
  font-size: 0.75rem;
}

.l-checkbox--size-x-small {
  gap: 6px;
}

/* Small: 18px */
.l-checkbox--size-small .l-checkbox__box {
  width: 18px;
  height: 18px;
  border-width: 1.5px;
  border-radius: 5px 2px 5px 2px;
}

.l-checkbox--size-small .l-checkbox__checkmark {
  width: 12px;
  height: 12px;
}

.l-checkbox--size-small .l-checkbox__label {
  font-size: 0.8rem;
}

.l-checkbox--size-small {
  gap: 8px;
}

/* Default: 22px (already defined above) */

/* Large: 28px */
.l-checkbox--size-large .l-checkbox__box {
  width: 28px;
  height: 28px;
  border-width: 2.5px;
  border-radius: 8px 3px 8px 3px;
}

.l-checkbox--size-large .l-checkbox__checkmark {
  width: 20px;
  height: 20px;
}

.l-checkbox--size-large .l-checkbox__label {
  font-size: 1rem;
}

.l-checkbox--size-large {
  gap: 12px;
}
</style>
