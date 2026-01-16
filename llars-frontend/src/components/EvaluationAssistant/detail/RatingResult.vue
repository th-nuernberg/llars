<template>
  <div class="rating-result">
    <div class="average-section">
      <span class="avg-label">{{ $t('evaluationAssistant.detail.averageRating') }}</span>
      <div class="avg-display">
        <LIcon v-for="star in 5" :key="star" size="24" :color="star <= Math.round(result.average_rating || 0) ? '#FFB300' : 'grey'">
          {{ star <= Math.round(result.average_rating || 0) ? 'mdi-star' : 'mdi-star-outline' }}
        </LIcon>
        <span class="avg-value">{{ (result.average_rating || 0).toFixed(1) }}</span>
      </div>
    </div>

    <div v-for="rating in (result.ratings || [])" :key="rating.feature_id" class="rating-item">
      <div class="rating-header">
        <span class="feature-label">Feature #{{ rating.feature_id }}</span>
        <div class="rating-stars">
          <LIcon v-for="star in 5" :key="star" size="18" :color="star <= rating.rating ? '#FFB300' : 'grey'">
            {{ star <= rating.rating ? 'mdi-star' : 'mdi-star-outline' }}
          </LIcon>
        </div>
      </div>
      <div v-if="rating.reasoning" class="rating-reasoning">{{ rating.reasoning }}</div>
      <div v-if="rating.strengths?.length" class="attr-section">
        <span class="attr-label text-success">{{ $t('evaluationAssistant.detail.strengths') }}</span>
        <div class="attr-list">
          <span v-for="(s, i) in rating.strengths" :key="i" class="attr-chip success">{{ s }}</span>
        </div>
      </div>
      <div v-if="rating.weaknesses?.length" class="attr-section">
        <span class="attr-label text-error">{{ $t('evaluationAssistant.detail.weaknesses') }}</span>
        <div class="attr-list">
          <span v-for="(w, i) in rating.weaknesses" :key="i" class="attr-chip error">{{ w }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ result: { type: Object, required: true } })
</script>

<style scoped>
.average-section { text-align: center; margin-bottom: 20px; padding: 16px; background: rgba(var(--v-theme-primary), 0.05); border-radius: 12px; }
.avg-label { font-size: 0.75rem; color: rgba(var(--v-theme-on-surface), 0.6); display: block; margin-bottom: 8px; }
.avg-display { display: flex; align-items: center; justify-content: center; gap: 4px; }
.avg-value { font-size: 1.5rem; font-weight: 700; margin-left: 8px; }
.rating-item { padding: 12px; background: rgba(var(--v-theme-on-surface), 0.02); border-radius: 8px; margin-bottom: 8px; }
.rating-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.feature-label { font-weight: 500; }
.rating-reasoning { font-size: 0.875rem; color: rgba(var(--v-theme-on-surface), 0.8); margin-bottom: 8px; }
.attr-section { margin-top: 8px; }
.attr-label { font-size: 0.75rem; font-weight: 500; display: block; margin-bottom: 4px; }
.attr-list { display: flex; flex-wrap: wrap; gap: 4px; }
.attr-chip { padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; }
.attr-chip.success { background: rgba(76, 175, 80, 0.1); color: #4CAF50; }
.attr-chip.error { background: rgba(244, 67, 54, 0.1); color: #F44336; }
</style>
