<template>
  <div class="ranking-result">
    <div v-for="(bucket, name) in result.buckets" :key="name" class="bucket-section">
      <div class="bucket-header" :class="`bucket-${name}`">
        <LIcon size="18" class="mr-2">{{ getBucketIcon(name) }}</LIcon>
        <span class="bucket-name">{{ $t(`evaluationAssistant.buckets.${name}`) }}</span>
        <span class="bucket-count">({{ bucket.feature_ids?.length || 0 }})</span>
      </div>
      <div class="bucket-features">
        <div v-for="featureId in (bucket.feature_ids || [])" :key="featureId" class="feature-chip">
          Feature #{{ featureId }}
        </div>
        <div v-if="!bucket.feature_ids?.length" class="no-features">
          {{ $t('evaluationAssistant.detail.noFeatures') }}
        </div>
      </div>
      <div v-if="bucket.reasoning" class="bucket-reasoning">
        {{ bucket.reasoning }}
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  result: {
    type: Object,
    required: true
  }
})

function getBucketIcon(bucket) {
  const icons = {
    gut: 'mdi-thumb-up',
    mittel: 'mdi-minus',
    schlecht: 'mdi-thumb-down',
    neutral: 'mdi-help-circle'
  }
  return icons[bucket] || 'mdi-circle'
}
</script>

<style scoped>
.bucket-section {
  margin-bottom: 16px;
  padding: 12px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
}

.bucket-header {
  display: flex;
  align-items: center;
  font-weight: 600;
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 8px;
}

.bucket-gut { background: rgba(76, 175, 80, 0.15); color: #4CAF50; }
.bucket-mittel { background: rgba(255, 193, 7, 0.15); color: #FFC107; }
.bucket-schlecht { background: rgba(244, 67, 54, 0.15); color: #F44336; }
.bucket-neutral { background: rgba(158, 158, 158, 0.15); color: #9E9E9E; }

.bucket-count {
  margin-left: auto;
  opacity: 0.7;
}

.bucket-features {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px 0;
}

.feature-chip {
  padding: 4px 10px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 16px;
  font-size: 0.75rem;
}

.no-features {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-style: italic;
}

.bucket-reasoning {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  padding: 8px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 4px;
  margin-top: 8px;
}
</style>
