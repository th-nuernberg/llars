<template>
  <div class="classification-result">
    <div class="label-section">
      <LTag variant="primary" size="lg">{{ result.label }}</LTag>
      <div class="confidence-score">{{ $t('evaluationAssistant.detail.confidenceScore') }}: {{ result.confidence_score }}/5</div>
    </div>

    <div v-if="result.alternative_labels?.length" class="alternatives-section">
      <div class="section-label">{{ $t('evaluationAssistant.detail.alternatives') }}</div>
      <div class="alternatives-list">
        <div v-for="(alt, i) in result.alternative_labels" :key="i" class="alt-item">
          <span class="alt-label">{{ alt.label }}</span>
          <v-progress-linear :model-value="alt.probability * 100" height="6" rounded color="grey" />
          <span class="alt-prob">{{ (alt.probability * 100).toFixed(0) }}%</span>
        </div>
      </div>
    </div>

    <div v-if="result.key_phrases?.length" class="phrases-section">
      <div class="section-label">{{ $t('evaluationAssistant.detail.keyPhrases') }}</div>
      <div class="phrases-list">
        <LTag v-for="(phrase, i) in result.key_phrases" :key="i" variant="gray" size="sm">{{ phrase }}</LTag>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ result: { type: Object, required: true } })
</script>

<style scoped>
.label-section { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.confidence-score { font-size: 0.875rem; color: rgba(var(--v-theme-on-surface), 0.7); }
.section-label { font-weight: 600; font-size: 0.875rem; margin-bottom: 8px; }
.alternatives-section { margin-bottom: 16px; }
.alternatives-list { display: flex; flex-direction: column; gap: 8px; }
.alt-item { display: grid; grid-template-columns: 100px 1fr 40px; gap: 8px; align-items: center; }
.alt-label { font-size: 0.875rem; }
.alt-prob { font-size: 0.75rem; text-align: right; }
.phrases-list { display: flex; flex-wrap: wrap; gap: 6px; }
</style>
