<template>
  <div class="authenticity-result">
    <div class="vote-section">
      <LTag :variant="result.vote === 'real' ? 'success' : 'danger'" size="lg">
        <LIcon size="20" class="mr-2">{{ result.vote === 'real' ? 'mdi-check-circle' : 'mdi-alert-circle' }}</LIcon>
        {{ $t(`evaluationAssistant.votes.${result.vote}`) }}
      </LTag>
      <div class="confidence-score">{{ $t('evaluationAssistant.detail.confidenceScore') }}: {{ result.confidence_score }}/5</div>
    </div>

    <div v-if="result.indicators?.length" class="indicators-section">
      <div class="section-label">{{ $t('evaluationAssistant.detail.indicators') }}</div>
      <div v-for="(ind, i) in result.indicators" :key="i" class="indicator-item">
        <LIcon size="16" :color="ind.supports === 'real' ? 'success' : 'error'" class="mr-2">
          {{ ind.supports === 'real' ? 'mdi-thumb-up' : 'mdi-thumb-down' }}
        </LIcon>
        <span class="indicator-text">{{ ind.indicator }}</span>
        <span class="indicator-weight">({{ (ind.weight * 100).toFixed(0) }}%)</span>
      </div>
    </div>

    <div v-if="result.linguistic_analysis" class="analysis-section">
      <div class="section-label">{{ $t('evaluationAssistant.detail.linguisticAnalysis') }}</div>
      <p>{{ result.linguistic_analysis }}</p>
    </div>

    <div v-if="result.behavioral_analysis" class="analysis-section">
      <div class="section-label">{{ $t('evaluationAssistant.detail.behavioralAnalysis') }}</div>
      <p>{{ result.behavioral_analysis }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({ result: { type: Object, required: true } })
</script>

<style scoped>
.vote-section { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.confidence-score { font-size: 0.875rem; color: rgba(var(--v-theme-on-surface), 0.7); }
.section-label { font-weight: 600; font-size: 0.875rem; margin-bottom: 8px; color: rgba(var(--v-theme-on-surface), 0.8); }
.indicators-section { margin-bottom: 16px; }
.indicator-item { display: flex; align-items: center; padding: 8px; background: rgba(var(--v-theme-on-surface), 0.02); border-radius: 6px; margin-bottom: 4px; }
.indicator-text { flex: 1; }
.indicator-weight { font-size: 0.75rem; color: rgba(var(--v-theme-on-surface), 0.5); margin-left: auto; }
.analysis-section { padding: 12px; background: rgba(var(--v-theme-on-surface), 0.02); border-radius: 8px; margin-bottom: 12px; }
.analysis-section p { margin: 0; font-size: 0.875rem; line-height: 1.6; }
</style>
