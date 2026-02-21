<template>
  <div class="mail-rating-result">
    <div class="overall-section">
      <span class="overall-label">{{ $t('evaluationAssistant.detail.overallRating') }}</span>
      <div class="overall-display">
        <LIcon v-for="star in 5" :key="star" size="28" :color="star <= result.overall_rating ? '#FFB300' : 'grey'">
          {{ star <= result.overall_rating ? 'mdi-star' : 'mdi-star-outline' }}
        </LIcon>
        <span class="overall-value">{{ result.overall_rating }}/5</span>
      </div>
    </div>

    <div v-if="result.criteria?.length" class="criteria-section">
      <div class="section-label">{{ $t('evaluationAssistant.detail.criteria') }}</div>
      <div v-for="(crit, i) in result.criteria" :key="i" class="criteria-item">
        <div class="criteria-header">
          <span class="criteria-name">{{ crit.name }}</span>
          <span class="criteria-score">{{ crit.score }}/5</span>
        </div>
        <v-progress-linear :model-value="crit.score * 20" height="6" rounded color="primary" />
        <div v-if="crit.reasoning" class="criteria-reasoning">{{ crit.reasoning }}</div>
      </div>
    </div>

    <div v-if="result.strengths?.length" class="attr-section">
      <div class="section-label text-success">{{ $t('evaluationAssistant.detail.strengths') }}</div>
      <ul class="attr-list"><li v-for="(s, i) in result.strengths" :key="i">{{ s }}</li></ul>
    </div>

    <div v-if="result.areas_for_improvement?.length" class="attr-section">
      <div class="section-label text-warning">{{ $t('evaluationAssistant.detail.improvements') }}</div>
      <ul class="attr-list"><li v-for="(a, i) in result.areas_for_improvement" :key="i">{{ a }}</li></ul>
    </div>

    <div v-if="result.summary" class="summary-section">
      <div class="section-label">{{ $t('evaluationAssistant.detail.summary') }}</div>
      <p>{{ result.summary }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({ result: { type: Object, required: true } })
</script>

<style scoped>
.overall-section { text-align: center; padding: 20px; background: rgba(var(--v-theme-primary), 0.05); border-radius: 12px; margin-bottom: 20px; }
.overall-label { font-size: 0.875rem; color: rgba(var(--v-theme-on-surface), 0.6); display: block; margin-bottom: 8px; }
.overall-display { display: flex; align-items: center; justify-content: center; gap: 4px; }
.overall-value { font-size: 1.25rem; font-weight: 700; margin-left: 12px; }
.section-label { font-weight: 600; font-size: 0.875rem; margin-bottom: 8px; }
.criteria-item { padding: 12px; background: rgba(var(--v-theme-on-surface), 0.02); border-radius: 8px; margin-bottom: 8px; }
.criteria-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.criteria-name { font-weight: 500; }
.criteria-score { font-weight: 600; }
.criteria-reasoning { font-size: 0.75rem; color: rgba(var(--v-theme-on-surface), 0.7); margin-top: 8px; }
.attr-section { margin-bottom: 16px; }
.attr-list { margin: 0; padding-left: 20px; }
.attr-list li { font-size: 0.875rem; margin-bottom: 4px; }
.summary-section { padding: 12px; background: rgba(var(--v-theme-on-surface), 0.02); border-radius: 8px; }
.summary-section p { margin: 0; font-size: 0.875rem; line-height: 1.6; }
</style>
