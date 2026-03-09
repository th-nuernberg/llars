<template>
  <div class="l-view-toggle" :class="[`l-view-toggle--${size}`]">
    <button
      class="l-view-toggle__btn"
      :class="{ active: modelValue === 'list' }"
      :title="listLabel"
      @click="$emit('update:modelValue', 'list')"
    >
      <LIcon :size="iconSize">llars:view-list</LIcon>
    </button>
    <button
      class="l-view-toggle__btn"
      :class="{ active: modelValue === 'cards' }"
      :title="cardsLabel"
      @click="$emit('update:modelValue', 'cards')"
    >
      <LIcon :size="iconSize">llars:view-cards</LIcon>
    </button>
  </div>
</template>

<script setup>
/**
 * LViewToggle - Card/List view mode toggle
 *
 * Uses LLARS custom icons (view-cards / view-list) with
 * the signature asymmetric border-radius styling.
 *
 * Usage:
 *   <LViewToggle v-model="viewMode" />
 */
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: 'cards',
    validator: v => ['cards', 'list'].includes(v)
  },
  size: {
    type: String,
    default: 'default',
    validator: v => ['small', 'default', 'large'].includes(v)
  },
  cardsLabel: {
    type: String,
    default: 'Card View'
  },
  listLabel: {
    type: String,
    default: 'List View'
  }
})

defineEmits(['update:modelValue'])

const iconSize = computed(() => {
  if (props.size === 'small') return 16
  if (props.size === 'large') return 22
  return 18
})
</script>

<style scoped>
.l-view-toggle {
  display: inline-flex;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 8px 3px 8px 3px;
  overflow: hidden;
}

.l-view-toggle__btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 32px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: rgba(var(--v-theme-on-surface), 0.45);
  transition: all 0.2s ease;
}

.l-view-toggle__btn:first-child {
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.15);
}

.l-view-toggle__btn:hover {
  background: rgba(var(--v-theme-on-surface), 0.06);
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.l-view-toggle__btn.active {
  background: rgba(var(--v-theme-primary), 0.15);
  color: rgb(var(--v-theme-primary));
}

/* Size: small */
.l-view-toggle--small .l-view-toggle__btn {
  width: 30px;
  height: 26px;
}

/* Size: large */
.l-view-toggle--large .l-view-toggle__btn {
  width: 42px;
  height: 38px;
}
</style>
