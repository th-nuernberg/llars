<template>
  <div
    class="l-radio-group"
    :class="{
      'l-radio-group--row': row,
      'l-radio-group--error': error
    }"
    role="radiogroup"
    :aria-label="label"
  >
    <div v-if="label" class="l-radio-group__label">
      {{ label }}
    </div>
    <div class="l-radio-group__options">
      <LRadio
        v-for="option in normalizedOptions"
        :key="option.value"
        :model-value="modelValue"
        :value="option.value"
        :label="option.label"
        :name="groupName"
        :disabled="disabled || option.disabled"
        :error="error"
        @update:model-value="handleChange"
      />
    </div>
    <div v-if="hint || error" class="l-radio-group__hint" :class="{ 'l-radio-group__hint--error': error }">
      {{ errorMessage || hint }}
    </div>
  </div>
</template>

<script setup>
/**
 * LRadioGroup - LLARS Global Radio Group Component
 *
 * A container for LRadio components with the signature LLARS styling.
 * Supports horizontal and vertical layouts.
 *
 * Usage:
 *   <LRadioGroup
 *     v-model="selected"
 *     label="Choose an option"
 *     :options="[
 *       { value: 'a', label: 'Option A' },
 *       { value: 'b', label: 'Option B' },
 *       { value: 'c', label: 'Option C', disabled: true }
 *     ]"
 *   />
 *
 *   <!-- Horizontal layout -->
 *   <LRadioGroup v-model="selected" :options="options" row />
 */
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number, Boolean, Object],
    default: null
  },
  options: {
    type: Array,
    required: true,
    validator: (v) => v.every(opt =>
      typeof opt === 'object' && 'value' in opt ||
      typeof opt === 'string' ||
      typeof opt === 'number'
    )
  },
  label: {
    type: String,
    default: ''
  },
  name: {
    type: String,
    default: ''
  },
  row: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  error: {
    type: Boolean,
    default: false
  },
  errorMessage: {
    type: String,
    default: ''
  },
  hint: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

// Generate unique group name if not provided
const groupName = computed(() => {
  return props.name || `l-radio-group-${Math.random().toString(36).substr(2, 9)}`
})

// Normalize options to always be objects
const normalizedOptions = computed(() => {
  return props.options.map(opt => {
    if (typeof opt === 'string' || typeof opt === 'number') {
      return { value: opt, label: String(opt) }
    }
    return {
      value: opt.value,
      label: opt.label || opt.title || String(opt.value),
      disabled: opt.disabled || false
    }
  })
})

function handleChange(value) {
  emit('update:modelValue', value)
  emit('change', value)
}
</script>

<style scoped>
.l-radio-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.l-radio-group__label {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 4px;
}

.l-radio-group__options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.l-radio-group--row .l-radio-group__options {
  flex-direction: row;
  flex-wrap: wrap;
  gap: 20px;
}

.l-radio-group__hint {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-top: 4px;
}

.l-radio-group__hint--error {
  color: var(--llars-danger, #e8a087);
}

/* Error state for label */
.l-radio-group--error .l-radio-group__label {
  color: var(--llars-danger, #e8a087);
}
</style>
