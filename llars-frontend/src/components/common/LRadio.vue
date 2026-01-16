<template>
  <label
    class="l-radio"
    :class="{
      'l-radio--checked': isChecked,
      'l-radio--disabled': disabled,
      'l-radio--error': error
    }"
  >
    <input
      type="radio"
      :checked="isChecked"
      :disabled="disabled"
      :name="name"
      :value="value"
      class="l-radio__input"
      @change="handleChange"
    />
    <span class="l-radio__box" :class="{ 'l-radio__box--animating': isAnimating }">
      <span class="l-radio__dot"></span>
    </span>
    <span v-if="$slots.default || label" class="l-radio__label">
      <slot>{{ label }}</slot>
    </span>
  </label>
</template>

<script setup>
/**
 * LRadio - LLARS Global Radio Button Component
 *
 * A custom radio button with the signature LLARS asymmetric border-radius styling.
 * Features an animated dot indicator on selection.
 *
 * Usage:
 *   <LRadio v-model="selected" value="option1" label="Option 1" name="group1" />
 *   <LRadio v-model="selected" value="option2" name="group1">Option 2</LRadio>
 *
 * For grouped radios, use LRadioGroup:
 *   <LRadioGroup v-model="selected" :options="[{value: 'a', label: 'A'}]" />
 */
import { computed, ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number, Boolean, Object],
    default: null
  },
  value: {
    type: [String, Number, Boolean, Object],
    required: true
  },
  label: {
    type: String,
    default: ''
  },
  name: {
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
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const isAnimating = ref(false)

const isChecked = computed(() => {
  return props.modelValue === props.value
})

function handleChange() {
  if (props.disabled) return

  // Trigger animation
  isAnimating.value = true
  setTimeout(() => {
    isAnimating.value = false
  }, 300)

  emit('update:modelValue', props.value)
  emit('change', props.value)
}

// Watch for external changes to trigger animation
let lastChecked = isChecked.value
watch(isChecked, (newVal) => {
  if (newVal && newVal !== lastChecked) {
    isAnimating.value = true
    setTimeout(() => {
      isAnimating.value = false
    }, 300)
  }
  lastChecked = newVal
})
</script>

<style scoped>
.l-radio {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.l-radio__input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
  pointer-events: none;
}

.l-radio__box {
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

.l-radio:hover:not(.l-radio--disabled) .l-radio__box {
  border-color: var(--llars-primary);
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.l-radio--checked .l-radio__box {
  border-color: var(--llars-primary);
  background-color: var(--llars-primary);
}

.l-radio--checked:hover:not(.l-radio--disabled) .l-radio__box {
  background-color: var(--llars-primary-dark, #9ab882);
}

/* Dot indicator */
.l-radio__dot {
  width: 10px;
  height: 10px;
  background-color: white;
  border-radius: 3px 1px 3px 1px; /* Smaller asymmetric corners */
  opacity: 0;
  transform: scale(0);
  transition: all 0.2s ease;
}

.l-radio--checked .l-radio__dot {
  opacity: 1;
  transform: scale(1);
}

/* Animation on click */
.l-radio__box--animating {
  animation: radio-pop 0.3s ease;
}

@keyframes radio-pop {
  0% { transform: scale(1); }
  50% { transform: scale(1.15); }
  100% { transform: scale(1); }
}

/* Label */
.l-radio__label {
  font-size: 0.9rem;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.4;
}

/* Disabled state */
.l-radio--disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.l-radio--disabled .l-radio__box {
  background-color: rgba(var(--v-theme-on-surface), 0.08);
}

/* Error state */
.l-radio--error .l-radio__box {
  border-color: var(--llars-danger, #e8a087);
}

.l-radio--error .l-radio__label {
  color: var(--llars-danger, #e8a087);
}

/* Focus visible */
.l-radio__input:focus-visible + .l-radio__box {
  outline: 2px solid var(--llars-primary);
  outline-offset: 2px;
}
</style>
