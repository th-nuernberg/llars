<template>
  <div class="likert-scale" :class="{ disabled }">
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      class="likert-btn"
      :class="{
        selected: modelValue === option.value,
        [`level-${option.level}`]: true
      }"
      :disabled="disabled"
      @click="selectRating(option.value)"
    >
      <span class="btn-value">{{ option.value }}</span>
      <span v-if="option.label" class="btn-label">{{ option.label }}</span>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  modelValue: { type: Number, default: null },
  disabled: { type: Boolean, default: false },
  min: { type: Number, default: 1 },
  max: { type: Number, default: 5 },
  labels: { type: Object, default: null },
  showLabels: { type: Boolean, default: true }
})

const emit = defineEmits(['update:modelValue'])
const { t, locale } = useI18n()

// Default labels for 5-point scale
const defaultLabels = computed(() => ({
  1: t('likertScale.veryGood', 'Sehr gut'),
  2: t('likertScale.good', 'Gut'),
  3: t('likertScale.neutral', 'Neutral'),
  4: t('likertScale.bad', 'Schlecht'),
  5: t('likertScale.veryBad', 'Sehr schlecht')
}))

const options = computed(() => {
  const result = []
  const range = props.max - props.min
  for (let i = props.min; i <= props.max; i++) {
    // Calculate level (1-5) for color mapping regardless of actual scale
    const normalizedPos = range > 0 ? (i - props.min) / range : 0.5
    const level = Math.round(normalizedPos * 4) + 1 // 1-5

    // Get label - support localized labels from config
    let label = null
    if (props.showLabels) {
      if (props.labels?.[i]) {
        // If label is an object with locale keys, get the right one
        const rawLabel = props.labels[i]
        if (typeof rawLabel === 'object' && rawLabel !== null) {
          label = rawLabel[locale.value] || rawLabel.de || rawLabel.en || Object.values(rawLabel)[0]
        } else {
          label = rawLabel
        }
      } else {
        label = defaultLabels.value[i] || null
      }
    }

    result.push({ value: i, label, level })
  }
  return result
})

function selectRating(value) {
  if (props.disabled) return
  // Toggle: if same value clicked, deselect
  emit('update:modelValue', value === props.modelValue ? null : value)
}
</script>

<style scoped>
.likert-scale {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.likert-scale.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.likert-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 64px;
  padding: 10px 12px;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.12);
  /* LLARS signature asymmetric border-radius */
  border-radius: 12px 3px 12px 3px;
  background: rgb(var(--v-theme-surface));
  cursor: pointer;
  transition: all 0.2s ease;
  flex: 1;
}

.likert-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.likert-btn:disabled {
  cursor: not-allowed;
}

/* Value number */
.btn-value {
  font-size: 1.1rem;
  font-weight: 700;
  line-height: 1;
}

/* Label text */
.btn-label {
  font-size: 0.65rem;
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.6);
  line-height: 1.2;
  margin-top: 4px;
  max-width: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* LLARS Color Palette - level 1 (best) to level 5 (worst) */
.level-1 { --btn-color: #b0ca97; } /* LLARS Primary - green */
.level-2 { --btn-color: #98d4bb; } /* LLARS Success */
.level-3 { --btn-color: #D1BC8A; } /* LLARS Secondary - neutral */
.level-4 { --btn-color: #e8c087; } /* Warning tone */
.level-5 { --btn-color: #e8a087; } /* LLARS Danger */

.likert-btn:not(.selected) .btn-value {
  color: var(--btn-color);
}

.likert-btn:not(.selected):hover:not(:disabled) {
  border-color: var(--btn-color);
  background: color-mix(in srgb, var(--btn-color) 12%, rgb(var(--v-theme-surface)));
}

.likert-btn.selected {
  border-color: var(--btn-color);
  background: var(--btn-color);
  box-shadow: 0 2px 8px color-mix(in srgb, var(--btn-color) 40%, transparent);
}

.likert-btn.selected .btn-value {
  color: white;
}

.likert-btn.selected .btn-label {
  color: rgba(255, 255, 255, 0.9);
}
</style>
