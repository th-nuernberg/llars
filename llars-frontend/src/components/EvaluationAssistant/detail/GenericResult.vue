<template>
  <div class="generic-result">
    <pre class="json-content">{{ JSON.stringify(result.result_data || result, null, 2) }}</pre>
  </div>
</template>

<script setup>
defineProps({
  result: {
    type: Object,
    required: true
  }
})
</script>

<style scoped>
.json-content {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.75rem;
  padding: 12px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 6px;
  overflow-x: auto;
  white-space: pre-wrap;
}
</style>
