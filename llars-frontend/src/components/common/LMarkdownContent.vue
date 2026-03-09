<template>
  <div class="markdown-content" :class="{ compact }" v-html="html" />
</template>

<script setup>
import { computed } from 'vue'
import DOMPurify from 'dompurify'
import { marked } from 'marked'

const props = defineProps({
  markdown: {
    type: String,
    default: ''
  },
  compact: {
    type: Boolean,
    default: false
  }
})

marked.setOptions({
  gfm: true,
  breaks: true
})

const html = computed(() => {
  const raw = marked.parse(props.markdown || '')
  return DOMPurify.sanitize(raw, {
    ALLOWED_TAGS: [
      'a', 'p', 'br', 'strong', 'em', 'u', 's',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li',
      'blockquote',
      'code', 'pre',
      'hr',
      'table', 'thead', 'tbody', 'tr', 'th', 'td',
      'span', 'div'
    ],
    ALLOWED_ATTR: ['href', 'title', 'target', 'rel', 'class']
  })
})
</script>

<style scoped>
.markdown-content {
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.65;
}

.markdown-content.compact {
  font-size: 0.92rem;
}

.markdown-content :deep(*:first-child) {
  margin-top: 0;
}

.markdown-content :deep(*:last-child) {
  margin-bottom: 0;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  line-height: 1.25;
  margin: 0 0 0.65em;
}

.markdown-content :deep(p),
.markdown-content :deep(ul),
.markdown-content :deep(ol),
.markdown-content :deep(blockquote),
.markdown-content :deep(pre),
.markdown-content :deep(table) {
  margin: 0 0 0.85em;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 1.25rem;
}

.markdown-content :deep(li + li) {
  margin-top: 0.25rem;
}

.markdown-content :deep(blockquote) {
  border-left: 3px solid rgba(var(--v-theme-primary), 0.45);
  padding-left: 12px;
  color: rgba(var(--v-theme-on-surface), 0.78);
}

.markdown-content :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 0.9em;
}

.markdown-content :deep(pre) {
  padding: 12px;
  border-radius: 10px;
  overflow: auto;
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.markdown-content :deep(a) {
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
}

.markdown-content :deep(a:hover) {
  text-decoration: underline;
}

.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  padding: 8px 10px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}
</style>
