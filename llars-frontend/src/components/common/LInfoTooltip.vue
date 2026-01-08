<template>
  <v-tooltip :location="location">
    <template #activator="{ props: activatorProps }">
      <v-btn
        v-bind="activatorProps"
        class="l-info-tooltip__btn"
        variant="text"
        :size="size"
        :aria-label="resolvedAriaLabel"
      >
        <LIcon :icon="icon" :size="iconSize" />
      </v-btn>
    </template>
    <div class="l-info-tooltip__content" :style="contentStyle">
      <div v-if="title" class="l-info-tooltip__title">{{ title }}</div>
      <div class="l-info-tooltip__text">
        <slot v-if="hasSlot" />
        <span v-else>{{ text }}</span>
      </div>
    </div>
  </v-tooltip>
</template>

<script setup>
import { computed, useSlots } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: ''
  },
  text: {
    type: String,
    default: ''
  },
  icon: {
    type: String,
    default: 'mdi-information-outline'
  },
  location: {
    type: String,
    default: 'bottom'
  },
  size: {
    type: String,
    default: 'small',
    validator: (v) => ['x-small', 'small', 'default', 'large', 'x-large'].includes(v)
  },
  maxWidth: {
    type: [Number, String],
    default: 360
  },
  ariaLabel: {
    type: String,
    default: ''
  }
})

const slots = useSlots()

const sizeMap = {
  'x-small': 14,
  'small': 18,
  'default': 20,
  'large': 24,
  'x-large': 28
}

const iconSize = computed(() => sizeMap[props.size] || 18)
const hasSlot = computed(() => Boolean(slots.default))
const resolvedAriaLabel = computed(() => props.ariaLabel || props.title || 'Info')
const contentStyle = computed(() => {
  if (props.maxWidth === null || props.maxWidth === undefined) return undefined
  const value = typeof props.maxWidth === 'number' ? `${props.maxWidth}px` : String(props.maxWidth)
  return { maxWidth: value }
})
</script>

<style scoped>
.l-info-tooltip__btn {
  min-width: 0;
  padding: 4px;
  border-radius: 8px 2px 8px 2px;
}

.l-info-tooltip__btn:hover:not(:disabled) {
  background-color: rgba(var(--v-theme-on-surface), 0.08);
}

.l-info-tooltip__content {
  padding: 8px 10px;
}

.l-info-tooltip__title {
  font-weight: 600;
  margin-bottom: 6px;
}

.l-info-tooltip__text {
  font-size: 0.85rem;
  line-height: 1.4;
  white-space: pre-line;
}

.l-info-tooltip__text :deep(ul) {
  margin: 6px 0 0 18px;
  padding: 0;
}

.l-info-tooltip__text :deep(li) {
  margin: 4px 0;
}
</style>
