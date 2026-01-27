<template>
  <div class="binary-scale" :class="{ disabled }">
    <button
      type="button"
      class="binary-btn yes"
      :class="{ selected: modelValue === 1 }"
      :disabled="disabled"
      @click="selectOption(1)"
    >
      <LIcon size="20" class="btn-icon">mdi-check</LIcon>
      <span class="btn-label">{{ computedYesLabel }}</span>
    </button>
    <button
      type="button"
      class="binary-btn no"
      :class="{ selected: modelValue === 2 }"
      :disabled="disabled"
      @click="selectOption(2)"
    >
      <LIcon size="20" class="btn-icon">mdi-close</LIcon>
      <span class="btn-label">{{ computedNoLabel }}</span>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  modelValue: { type: Number, default: null },
  disabled: { type: Boolean, default: false },
  yesLabel: { type: String, default: null },
  noLabel: { type: String, default: null }
})

const emit = defineEmits(['update:modelValue'])
const { t } = useI18n()

const computedYesLabel = computed(() => props.yesLabel || t('binaryScale.yes', 'Ja'))
const computedNoLabel = computed(() => props.noLabel || t('binaryScale.no', 'Nein'))

function selectOption(value) {
  if (props.disabled) return
  // Toggle: if same value clicked, deselect
  emit('update:modelValue', value === props.modelValue ? null : value)
}
</script>

<style scoped>
.binary-scale {
  display: flex;
  gap: 12px;
}

.binary-scale.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.binary-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex: 1;
  min-width: 100px;
  padding: 12px 20px;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.12);
  /* LLARS signature asymmetric border-radius */
  border-radius: 12px 3px 12px 3px;
  background: rgb(var(--v-theme-surface));
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 600;
}

.binary-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.binary-btn:disabled {
  cursor: not-allowed;
}

/* Yes button - Original green */
.binary-btn.yes {
  --btn-color: #66BB6A;
}

.binary-btn.yes:not(.selected) .btn-icon {
  color: var(--btn-color);
}

.binary-btn.yes:hover:not(:disabled):not(.selected) {
  border-color: var(--btn-color);
  background: color-mix(in srgb, var(--btn-color) 12%, rgb(var(--v-theme-surface)));
}

.binary-btn.yes.selected {
  border-color: var(--btn-color);
  background: var(--btn-color);
  color: white;
  box-shadow: 0 2px 8px color-mix(in srgb, var(--btn-color) 40%, transparent);
}

.binary-btn.yes.selected .btn-icon {
  color: white;
}

/* No button - Original purple */
.binary-btn.no {
  --btn-color: #AB47BC;
}

.binary-btn.no:not(.selected) .btn-icon {
  color: var(--btn-color);
}

.binary-btn.no:hover:not(:disabled):not(.selected) {
  border-color: var(--btn-color);
  background: color-mix(in srgb, var(--btn-color) 12%, rgb(var(--v-theme-surface)));
}

.binary-btn.no.selected {
  border-color: var(--btn-color);
  background: var(--btn-color);
  color: white;
  box-shadow: 0 2px 8px color-mix(in srgb, var(--btn-color) 40%, transparent);
}

.binary-btn.no.selected .btn-icon {
  color: white;
}

/* Label */
.btn-label {
  font-size: 0.9rem;
}
</style>
