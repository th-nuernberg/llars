<template>
  <div class="comparison-result">
    <div class="winner-section">
      <LTag :variant="result.winner === 'TIE' ? 'info' : 'primary'" size="lg">
        <LIcon size="20" class="mr-2">mdi-trophy</LIcon>
        {{ result.winner === 'TIE' ? $t('evaluationAssistant.comparison.tie') : $t('evaluationAssistant.comparison.winner', { winner: result.winner }) }}
      </LTag>
      <div class="confidence-score">{{ $t('evaluationAssistant.detail.confidenceScore') }}: {{ result.confidence_score }}/5</div>
    </div>

    <div v-if="result.comparison_aspects?.length" class="aspects-section">
      <div class="section-label">{{ $t('evaluationAssistant.detail.aspects') }}</div>
      <div v-for="(asp, i) in result.comparison_aspects" :key="i" class="aspect-item">
        <div class="aspect-header">
          <span class="aspect-name">{{ asp.aspect }}</span>
          <LTag :variant="asp.winner === 'TIE' ? 'gray' : 'primary'" size="sm">{{ asp.winner }}</LTag>
        </div>
        <div v-if="asp.reasoning" class="aspect-reasoning">{{ asp.reasoning }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ result: { type: Object, required: true } })
</script>

<style scoped>
.winner-section { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.confidence-score { font-size: 0.875rem; color: rgba(var(--v-theme-on-surface), 0.7); }
.section-label { font-weight: 600; font-size: 0.875rem; margin-bottom: 8px; }
.aspect-item { padding: 12px; background: rgba(var(--v-theme-on-surface), 0.02); border-radius: 8px; margin-bottom: 8px; }
.aspect-header { display: flex; justify-content: space-between; align-items: center; }
.aspect-name { font-weight: 500; }
.aspect-reasoning { font-size: 0.75rem; color: rgba(var(--v-theme-on-surface), 0.7); margin-top: 8px; }
</style>
