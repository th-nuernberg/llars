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
        <div v-else-if="hasRichContent" class="l-info-tooltip__rich" v-html="renderedRichContent"></div>
        <span v-else>{{ text }}</span>
      </div>
    </div>
  </v-tooltip>
</template>

<script setup>
import { computed, useSlots } from 'vue'
import { marked } from 'marked'
import { sanitizeHtmlCustom } from '@/utils/sanitize'

const props = defineProps({
  title: {
    type: String,
    default: ''
  },
  text: {
    type: String,
    default: ''
  },
  markdown: {
    type: String,
    default: ''
  },
  html: {
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

const tooltipSanitizeConfig = {
  ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li', 'div', 'span', 'code', 'pre', 'a'],
  ALLOWED_ATTR: ['href', 'target', 'rel', 'class']
}

const iconSize = computed(() => sizeMap[props.size] || 18)
const hasSlot = computed(() => Boolean(slots.default))
const hasMarkdown = computed(() => Boolean(props.markdown?.trim()))
const hasHtml = computed(() => Boolean(props.html?.trim()))
const hasRichContent = computed(() => hasMarkdown.value || hasHtml.value)
const resolvedAriaLabel = computed(() => props.ariaLabel || props.title || 'Info')
const contentStyle = computed(() => {
  if (props.maxWidth === null || props.maxWidth === undefined) return undefined
  const value = typeof props.maxWidth === 'number' ? `${props.maxWidth}px` : String(props.maxWidth)
  return { maxWidth: value }
})

const renderedRichContent = computed(() => {
  if (hasMarkdown.value) {
    try {
      const parsed = marked.parse(props.markdown, { breaks: true })
      return sanitizeHtmlCustom(String(parsed), tooltipSanitizeConfig)
    } catch {
      return sanitizeHtmlCustom(props.markdown, tooltipSanitizeConfig)
    }
  }

  if (hasHtml.value) {
    return sanitizeHtmlCustom(props.html, tooltipSanitizeConfig)
  }

  return ''
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

.l-info-tooltip__rich {
  white-space: normal;
}

.l-info-tooltip__rich :deep(p) {
  margin: 0 0 6px;
}

.l-info-tooltip__rich :deep(p:last-child) {
  margin-bottom: 0;
}

.l-info-tooltip__text :deep(ul) {
  margin: 6px 0 0 18px;
  padding: 0;
}

.l-info-tooltip__text :deep(li) {
  margin: 4px 0;
}
</style>
