<template>
  <span v-html="renderedFormula" class="katex-formula" :class="{ 'display-mode': displayMode }"></span>
</template>

<script setup>
import { computed } from 'vue';
import katex from 'katex';
import 'katex/dist/katex.min.css';

const props = defineProps({
  formula: {
    type: String,
    required: true
  },
  displayMode: {
    type: Boolean,
    default: false
  }
});

const renderedFormula = computed(() => {
  try {
    return katex.renderToString(props.formula, {
      throwOnError: false,
      displayMode: props.displayMode
    });
  } catch (e) {
    console.error('KaTeX error:', e);
    return props.formula;
  }
});
</script>

<style scoped>
.katex-formula {
  color: inherit;
}

.katex-formula.display-mode {
  display: block;
  text-align: center;
  margin: 8px 0;
}
</style>
