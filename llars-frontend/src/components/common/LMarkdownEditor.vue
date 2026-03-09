<template>
  <div class="markdown-editor">
    <div class="markdown-toolbar">
      <v-btn size="small" variant="text" @click="insertHeading(1)">H1</v-btn>
      <v-btn size="small" variant="text" @click="insertHeading(2)">H2</v-btn>
      <v-btn size="small" variant="text" @click="wrapSelection('**', '**', 'Text')">
        <strong>B</strong>
      </v-btn>
      <v-btn size="small" variant="text" @click="wrapSelection('*', '*', 'Text')">
        <em>I</em>
      </v-btn>
      <v-btn size="small" variant="text" @click="prefixLines('- ', 'Kriterium')">•</v-btn>
      <v-btn size="small" variant="text" @click="prefixNumberedLines()">1.</v-btn>
      <v-btn size="small" variant="text" @click="prefixLines('> ', 'Hinweis')">"</v-btn>
      <v-btn size="small" variant="text" icon="mdi-link-variant" @click="insertLink" />
    </div>

    <div class="markdown-body">
      <v-textarea
        ref="textareaRef"
        :model-value="modelValue"
        :placeholder="placeholder"
        :rows="rows"
        auto-grow
        variant="outlined"
        class="markdown-input"
        @update:modelValue="emit('update:modelValue', $event)"
      />

      <div class="markdown-preview">
        <LMarkdownContent :markdown="modelValue" compact />
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: ''
  },
  rows: {
    type: [String, Number],
    default: 6
  }
})

const emit = defineEmits(['update:modelValue'])

const textareaRef = ref(null)

function getNativeTextarea() {
  return textareaRef.value?.$el?.querySelector('textarea') || null
}

function replaceSelection(transform) {
  const textarea = getNativeTextarea()
  const currentValue = props.modelValue || ''

  if (!textarea) {
    emit('update:modelValue', transform(currentValue, 0, 0).text)
    return
  }

  const start = textarea.selectionStart ?? currentValue.length
  const end = textarea.selectionEnd ?? currentValue.length
  const result = transform(currentValue, start, end)

  emit('update:modelValue', result.text)

  nextTick(() => {
    const target = getNativeTextarea()
    if (!target) return
    target.focus()

    const selectionStart = result.selectionStart ?? start
    const selectionEnd = result.selectionEnd ?? selectionStart
    target.setSelectionRange(selectionStart, selectionEnd)
  })
}

function wrapSelection(prefix, suffix, fallbackText) {
  replaceSelection((value, start, end) => {
    const selected = value.slice(start, end) || fallbackText
    const replacement = `${prefix}${selected}${suffix}`
    const text = `${value.slice(0, start)}${replacement}${value.slice(end)}`
    const selectionStart = start + prefix.length
    const selectionEnd = selectionStart + selected.length
    return { text, selectionStart, selectionEnd }
  })
}

function insertHeading(level) {
  const prefix = `${'#'.repeat(level)} `
  replaceSelection((value, start, end) => {
    const selected = value.slice(start, end) || 'Titel'
    const replacement = `${prefix}${selected}`
    const text = `${value.slice(0, start)}${replacement}${value.slice(end)}`
    const selectionStart = start + prefix.length
    const selectionEnd = selectionStart + selected.length
    return { text, selectionStart, selectionEnd }
  })
}

function prefixLines(prefix, fallbackLine) {
  replaceSelection((value, start, end) => {
    const selected = value.slice(start, end) || fallbackLine
    const replacement = selected
      .split('\n')
      .map(line => `${prefix}${line || fallbackLine}`)
      .join('\n')
    const text = `${value.slice(0, start)}${replacement}${value.slice(end)}`
    return {
      text,
      selectionStart: start,
      selectionEnd: start + replacement.length
    }
  })
}

function prefixNumberedLines() {
  replaceSelection((value, start, end) => {
    const selected = value.slice(start, end) || 'Punkt'
    const replacement = selected
      .split('\n')
      .map((line, index) => `${index + 1}. ${line || 'Punkt'}`)
      .join('\n')
    const text = `${value.slice(0, start)}${replacement}${value.slice(end)}`
    return {
      text,
      selectionStart: start,
      selectionEnd: start + replacement.length
    }
  })
}

function insertLink() {
  replaceSelection((value, start, end) => {
    const selected = value.slice(start, end) || 'Linktext'
    const replacement = `[${selected}](https://)`
    const text = `${value.slice(0, start)}${replacement}${value.slice(end)}`
    const selectionStart = start + selected.length + 3
    const selectionEnd = selectionStart + 8
    return { text, selectionStart, selectionEnd }
  })
}
</script>

<style scoped>
.markdown-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.markdown-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 8px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 10px;
  background: rgba(var(--v-theme-surface-variant), 0.18);
}

.markdown-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 12px;
}

.markdown-input :deep(textarea) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  line-height: 1.55;
}

.markdown-preview {
  min-height: 100%;
  padding: 14px 16px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px;
  background: rgb(var(--v-theme-surface));
  overflow: auto;
}

@media (max-width: 960px) {
  .markdown-body {
    grid-template-columns: 1fr;
  }
}
</style>
