<template>
  <div class="result-badge">
    <!-- Ranking Result -->
    <template v-if="result.task_type === 'ranking'">
      <div class="badge-pills">
        <span class="pill pill-success" v-if="gutCount > 0">{{ gutCount }}</span>
        <span class="pill pill-warning" v-if="mittelCount > 0">{{ mittelCount }}</span>
        <span class="pill pill-error" v-if="schlechtCount > 0">{{ schlechtCount }}</span>
      </div>
    </template>

    <!-- Rating Result -->
    <template v-else-if="result.task_type === 'rating' || result.task_type === 'mail_rating'">
      <div class="rating-badge">
        <LIcon size="16" color="#FFB300">mdi-star</LIcon>
        <span>{{ averageRating }}</span>
      </div>
    </template>

    <!-- Authenticity Result -->
    <template v-else-if="result.task_type === 'authenticity'">
      <LTag :variant="result.vote === 'real' ? 'success' : 'danger'" size="sm">
        {{ result.vote === 'real' ? 'Real' : 'Fake' }}
      </LTag>
    </template>

    <!-- Comparison Result -->
    <template v-else-if="result.task_type === 'comparison'">
      <LTag variant="primary" size="sm">
        {{ result.winner === 'TIE' ? 'TIE' : result.winner }}
      </LTag>
    </template>

    <!-- Classification Result -->
    <template v-else-if="result.task_type === 'text_classification'">
      <LTag variant="info" size="sm">
        {{ result.label }}
      </LTag>
    </template>

    <!-- Unknown/Generic -->
    <template v-else>
      <LIcon size="16">mdi-check</LIcon>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  result: {
    type: Object,
    required: true
  }
})

const gutCount = computed(() => props.result.buckets?.gut?.feature_ids?.length || 0)
const mittelCount = computed(() => props.result.buckets?.mittel?.feature_ids?.length || 0)
const schlechtCount = computed(() => props.result.buckets?.schlecht?.feature_ids?.length || 0)

const averageRating = computed(() => {
  if (props.result.task_type === 'mail_rating') {
    return props.result.overall_rating?.toFixed(1) || '-'
  }
  if (props.result.ratings?.length) {
    const avg = props.result.ratings.reduce((sum, r) => sum + r.rating, 0) / props.result.ratings.length
    return avg.toFixed(1)
  }
  return props.result.average_rating?.toFixed(1) || '-'
})
</script>

<style scoped>
.result-badge {
  display: flex;
  align-items: center;
}

.badge-pills {
  display: flex;
  gap: 4px;
}

.pill {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 600;
}

.pill-success {
  background: rgba(76, 175, 80, 0.15);
  color: #4CAF50;
}

.pill-warning {
  background: rgba(255, 193, 7, 0.15);
  color: #FFC107;
}

.pill-error {
  background: rgba(244, 67, 54, 0.15);
  color: #F44336;
}

.rating-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
}
</style>
