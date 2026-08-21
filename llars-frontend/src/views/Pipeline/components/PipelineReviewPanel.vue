<template>
  <div class="review-panel">
    <div class="review-header">
      <v-icon size="24" color="warning">mdi-account-question</v-icon>
      <h3>{{ $t('pipeline.review.title') }}</h3>
    </div>

    <p class="review-reason">
      {{ $t('pipeline.review.reason.' + (reason || 'plateau')) }}
    </p>

    <div v-if="bestConfig" class="best-config">
      <div class="config-label">{{ $t('pipeline.review.bestConfig') }}</div>
      <div class="config-stats">
        <LTag variant="success" size="sm">
          {{ $t('pipeline.avgScore') }}: {{ bestConfig.avg_score?.toFixed(2) || '—' }}
        </LTag>
        <LTag variant="info" size="sm">
          {{ $t('pipeline.iterationLabel', { n: bestConfig.iteration || '—' }) }}
        </LTag>
      </div>
    </div>

    <div class="review-actions">
      <LBtn variant="primary" @click="$emit('review', 'deploy')">
        <v-icon start size="18">mdi-rocket-launch</v-icon>
        {{ $t('pipeline.review.deploy') }}
      </LBtn>
      <LBtn variant="secondary" @click="$emit('review', 'continue')">
        <v-icon start size="18">mdi-play</v-icon>
        {{ $t('pipeline.review.continue') }}
      </LBtn>
      <LBtn variant="cancel" @click="$emit('review', 'reject')">
        {{ $t('pipeline.review.reject') }}
      </LBtn>
    </div>
  </div>
</template>

<script setup>
import LBtn from '@/components/common/LBtn.vue'
import LTag from '@/components/common/LTag.vue'

defineProps({
  bestConfig: { type: Object, default: null },
  reason: { type: String, default: 'plateau' },
})

defineEmits(['review'])
</script>

<style scoped>
.review-panel {
  border: 2px solid rgba(var(--v-theme-warning), 0.4);
  border-radius: 16px 4px 16px 4px;
  padding: 20px;
  background: rgba(var(--v-theme-warning), 0.04);
}

.review-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.review-header h3 {
  margin: 0;
  font-size: 1rem;
}

.review-reason {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 16px;
}

.best-config {
  padding: 12px;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  margin-bottom: 16px;
}

.config-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
  margin-bottom: 6px;
}

.config-stats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.review-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
