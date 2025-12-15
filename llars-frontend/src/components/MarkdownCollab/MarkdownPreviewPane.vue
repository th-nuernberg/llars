<template>
  <div class="preview-root">
    <v-skeleton-loader v-if="loading" type="article" class="ma-0" />
    <div v-else class="preview-content" v-html="html" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import DOMPurify from 'dompurify'
import { marked } from 'marked'

const props = defineProps({
  markdown: { type: String, default: '' },
  loading: { type: Boolean, default: false }
})

const html = computed(() => {
  const raw = marked.parse(props.markdown || '', { breaks: true })
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
    ALLOWED_ATTR: ['href', 'title', 'target', 'rel', 'class', 'style'],
    ADD_ATTR: ['target', 'rel'],
  })
})
</script>

<style scoped>
.preview-root {
  height: 100%;
  overflow: auto;
  background: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
  border-radius: 10px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.preview-content {
  padding: 16px 18px;
  line-height: 1.6;
}

.preview-content :deep(pre) {
  background: rgba(var(--v-theme-on-surface), 0.06);
  padding: 12px;
  border-radius: 10px;
  overflow: auto;
}

.preview-content :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 0.9em;
}

.preview-content :deep(blockquote) {
  border-left: 4px solid rgba(var(--v-theme-primary), 0.6);
  padding-left: 12px;
  margin-left: 0;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.preview-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
}

.preview-content :deep(th),
.preview-content :deep(td) {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  padding: 8px 10px;
}

.preview-content :deep(a) {
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
}

.preview-content :deep(a:hover) {
  text-decoration: underline;
}
</style>

