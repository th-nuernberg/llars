<template>
  <button
    class="l-label-btn"
    :class="{ selected: isSelected }"
    :style="style"
    :disabled="disabled"
    type="button"
    @click="$emit('select', category.id)"
  >
    <span v-if="hotkey" class="l-label-btn__hotkey">{{ hotkey }}</span>
    <span class="l-label-btn__name">{{ name }}</span>
    <span v-if="description" class="l-label-btn__desc">{{ description }}</span>
  </button>
</template>

<script setup>
/**
 * One category choice in a labeling task.
 *
 * Exists so that every labeling surface renders the same button. The look was
 * duplicated across LabelingInterface and ConversationLabelingInterface, and it
 * drifted: one filled the button with a tint of the category colour at all
 * times, the other only on selection. Side by side they read as two different
 * products, and the tinted variant looked pre-selected — which matters when the
 * study design says a suggestion must never appear chosen.
 *
 * The colour rule is the load-bearing part: outline in the category colour,
 * fill solid ONLY when selected. That is what makes "chosen" unmistakable at a
 * glance across ~92 decisions in a row.
 */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  /** Category object from the scenario config: { id, label|name, description, color } */
  category: { type: Object, required: true },
  /** Currently chosen category id (compared against category.id). */
  modelValue: { type: [String, Number], default: null },
  disabled: { type: Boolean, default: false },
  /** Optional keyboard digit shown discreetly in the corner. */
  hotkey: { type: [String, Number], default: null },
  fallbackColor: { type: String, default: '#b0ca97' }
})

defineEmits(['select'])

const { locale } = useI18n()

/**
 * Category texts come from the scenario config, not the i18n catalogue, so the
 * ACTIVE locale has to win here — falling back to de/en only when the active
 * one is missing. Without this an English rater reads German category names and
 * no locale check would ever catch it.
 */
function localize(value) {
  if (!value) return ''
  if (typeof value === 'string') return value
  return value[locale.value] || value.de || value.en || ''
}

const isSelected = computed(() => props.modelValue === props.category.id)

// `label` is the schema field; `name` is the legacy one. The id is the last
// resort so a button is never blank.
const name = computed(
  () => localize(props.category.label) || localize(props.category.name) || props.category.id || ''
)
const description = computed(() => localize(props.category.description))

const style = computed(() => {
  const baseColor = props.category.color || props.fallbackColor
  return {
    '--l-label-color': baseColor,
    '--l-label-bg': isSelected.value ? baseColor : 'transparent',
    '--l-label-text': isSelected.value ? '#fff' : baseColor,
    borderColor: baseColor
  }
})
</script>

<style scoped>
.l-label-btn {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 100%;
  padding: 20px 24px;
  border: 2px solid var(--l-label-color);
  border-radius: 16px 4px 16px 4px; /* LLARS signature */
  background: var(--l-label-bg);
  color: var(--l-label-text);
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
  text-align: center;
}

.l-label-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.l-label-btn.selected {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.l-label-btn:disabled {
  opacity: 0.5;
  cursor: default;
  transform: none;
}

.l-label-btn__name {
  font-size: 1.1rem;
  font-weight: 600;
}

/* 0.85rem rather than 0.8: the definition is read on every decision, so it sits
   above the readability floor rather than at it. */
.l-label-btn__desc {
  font-size: 0.85rem;
  opacity: 0.8;
}

/* Kept quiet on purpose — it is a hint, not a second label. */
.l-label-btn__hotkey {
  position: absolute;
  top: 10px;
  left: 12px;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--l-label-color);
  opacity: 0.55;
}

@media (prefers-reduced-motion: reduce) {
  .l-label-btn {
    transition: none;
  }
  .l-label-btn:hover:not(:disabled),
  .l-label-btn.selected {
    transform: none;
  }
}
</style>
