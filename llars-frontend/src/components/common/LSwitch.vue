<template>
  <label
    class="l-switch"
    :class="{
      'l-switch--checked': modelValue,
      'l-switch--disabled': disabled
    }"
  >
    <input
      type="checkbox"
      :checked="modelValue"
      :disabled="disabled"
      class="l-switch__input"
      @change="handleChange"
    />
    <span class="l-switch__track" :class="{ 'l-switch__track--animating': isAnimating }">
      <span class="l-switch__thumb"></span>
    </span>
    <span v-if="$slots.default || label" class="l-switch__label">
      <slot>{{ label }}</slot>
    </span>
  </label>
</template>

<script setup>
/**
 * LSwitch - LLARS Global Toggle Switch Component
 *
 * A custom toggle switch with the signature LLARS asymmetric border-radius styling.
 * Features smooth animation on toggle.
 *
 * Usage:
 *   <LSwitch v-model="enabled" label="Enable notifications" />
 *   <LSwitch v-model="darkMode">Dark Mode</LSwitch>
 */
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  label: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const isAnimating = ref(false)

function handleChange(event) {
  if (props.disabled) return

  // Trigger animation
  isAnimating.value = true
  setTimeout(() => {
    isAnimating.value = false
  }, 300)

  const newValue = event.target.checked
  emit('update:modelValue', newValue)
  emit('change', newValue)
}

// Watch for external changes to trigger animation
let lastValue = props.modelValue
watch(() => props.modelValue, (newVal) => {
  if (newVal !== lastValue) {
    isAnimating.value = true
    setTimeout(() => {
      isAnimating.value = false
    }, 300)
    lastValue = newVal
  }
})
</script>

<style scoped>
.l-switch {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.l-switch__input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
  pointer-events: none;
}

.l-switch__track {
  position: relative;
  width: 44px;
  height: 24px;
  border-radius: 8px 3px 8px 3px; /* LLARS signature asymmetric corners */
  background-color: rgba(var(--v-theme-on-surface), 0.25);
  transition: all 0.25s ease;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.l-switch:hover:not(.l-switch--disabled) .l-switch__track {
  background-color: rgba(var(--v-theme-on-surface), 0.35);
}

.l-switch--checked .l-switch__track {
  background-color: var(--llars-primary);
}

.l-switch--checked:hover:not(.l-switch--disabled) .l-switch__track {
  background-color: var(--llars-primary-dark, #9ab882);
}

/* Thumb */
.l-switch__thumb {
  position: absolute;
  left: 3px;
  width: 18px;
  height: 18px;
  background-color: white;
  border-radius: 5px 2px 5px 2px; /* Smaller asymmetric corners */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.25s ease;
}

.l-switch--checked .l-switch__thumb {
  left: calc(100% - 21px);
}

/* Animation on toggle */
.l-switch__track--animating .l-switch__thumb {
  animation: switch-bounce 0.3s ease;
}

@keyframes switch-bounce {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

/* Label */
.l-switch__label {
  font-size: 0.9rem;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.4;
}

/* Disabled state */
.l-switch--disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.l-switch--disabled .l-switch__track {
  background-color: rgba(var(--v-theme-on-surface), 0.15);
}

/* Focus visible */
.l-switch__input:focus-visible + .l-switch__track {
  outline: 2px solid var(--llars-primary);
  outline-offset: 2px;
}
</style>
